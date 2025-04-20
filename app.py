from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
import logging
from config import get_timezone, get_cutoff_time, LOCATION

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lunch.db"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Helper function to check if ordering is closed for a date
def is_ordering_closed(date):
    # Get current time in configured timezone
    local_tz = get_timezone()
    now = datetime.now(local_tz)

    # Convert the input date to local timezone for comparison
    date_in_local = local_tz.localize(datetime.combine(date, datetime.min.time()))

    # Get the cutoff time
    cutoff = get_cutoff_time()

    # If the date is today and it's past the cutoff time
    if date_in_local.date() == now.date() and now.time() >= cutoff:
        return True
    return False


# Load lunch options from JSON file
def load_lunch_options():
    with open("data/lunch_options.json", "r") as f:
        data = json.load(f)["daily_options"]
        logging.debug(f"Raw lunch options from JSON: {data}")
        return data


# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    orders = db.relationship("Order", backref="user", lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(1), nullable=False)  # N, V, C, B, P


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    logger.debug("Dashboard route called")
    logger.debug(f"Current user: {current_user}")

    # Load lunch options first
    lunch_options = load_lunch_options()
    logger.debug(f"Loaded lunch options: {lunch_options}")

    # Get the dates from lunch options
    week_dates = [
        datetime.strptime(date_str, "%Y-%m-%d").date()
        for date_str in lunch_options.keys()
    ]
    week_dates.sort()  # Sort dates in ascending order
    logger.debug(f"Week dates: {week_dates}")

    # Get user's orders
    orders = {}
    for order in Order.query.filter_by(user_id=current_user.id).all():
        orders[order.date.strftime("%Y-%m-%d")] = order.meal_type
    logger.debug(f"User orders: {orders}")

    # Get cart from session
    cart = session.get("cart", {})
    logger.debug(f"Session cart: {cart}")

    # Check which dates have ordering closed
    ordering_closed = {}
    for date in week_dates:
        ordering_closed[date.strftime("%Y-%m-%d")] = is_ordering_closed(date)
    logger.debug(f"Ordering closed status: {ordering_closed}")

    # Debug template variables
    template_vars = {
        "week_dates": week_dates,
        "lunch_options": lunch_options,
        "orders": orders,
        "cart": cart,
        "ordering_closed": ordering_closed,
        "lunch_options_json": lunch_options,
        "location": LOCATION,
    }
    logger.debug(f"Template variables: {template_vars}")

    return render_template("dashboard.html", **template_vars)


@app.route("/order", methods=["POST"])
@login_required
def order():
    logger.debug(f"Received order request: {request.form}")

    # Get list of dates that already have orders
    ordered_dates = request.form.getlist("ordered_dates")
    logger.debug(f"Ordered dates: {ordered_dates}")

    # Process all orders in the form
    for key, meal_type in request.form.items():
        if key.startswith("meal_type_"):
            date_str = key.replace("meal_type_", "")

            # Skip if this date already has an order
            if date_str in ordered_dates:
                logger.debug(f"Skipping already ordered date: {date_str}")
                continue

            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            logger.debug(f"Processing order for date: {date}, meal_type: {meal_type}")

            # Check if order already exists for this date
            existing_order = Order.query.filter_by(
                user_id=current_user.id, date=date
            ).first()

            if existing_order:
                logger.debug(f"Updating existing order: {existing_order}")
                existing_order.meal_type = meal_type
            else:
                logger.debug("Creating new order")
                new_order = Order(
                    user_id=current_user.id, date=date, meal_type=meal_type
                )
                db.session.add(new_order)

    try:
        db.session.commit()
        logger.debug("Orders saved successfully")
        flash("Orders saved successfully!")
    except Exception as e:
        logger.error(f"Error saving orders: {e}")
        flash("Error saving orders. Please try again.")
        db.session.rollback()

    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    # Get the cart from session or initialize it
    cart = session.get("cart", {})

    logger.debug(f"Current cart before adding items: {cart}")
    logger.debug(f"Form data: {request.form}")

    # Process all selections in the form
    for key, meal_type in request.form.items():
        if key.startswith("meal_type_") and meal_type:  # Only add non-empty selections
            date_str = key.replace("meal_type_", "")
            cart[date_str] = meal_type
            logger.debug(f"Added to cart - date: {date_str}, meal: {meal_type}")

    # Save the cart to session
    session["cart"] = cart
    logger.debug(f"Updated cart: {cart}")

    flash("Items added to cart!")
    return redirect(url_for("dashboard") + "?tab=cart")


@app.route("/submit_cart", methods=["POST"])
@login_required
def submit_cart():
    cart = session.get("cart", {})

    # Process all orders in the cart
    for date_str, meal_type in cart.items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check if order already exists for this date
        existing_order = Order.query.filter_by(
            user_id=current_user.id, date=date
        ).first()

        if existing_order:
            existing_order.meal_type = meal_type
        else:
            new_order = Order(user_id=current_user.id, date=date, meal_type=meal_type)
            db.session.add(new_order)

    try:
        db.session.commit()
        # Clear the cart after successful submission
        session.pop("cart", None)
        flash("Orders submitted successfully!")
    except Exception as e:
        logger.error(f"Error saving orders: {e}")
        flash("Error saving orders. Please try again.")
        db.session.rollback()

    return redirect(url_for("dashboard"))


@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    data = request.get_json()
    date = data.get("date")

    if date:
        cart = session.get("cart", {})
        if date in cart:
            del cart[date]
            session["cart"] = cart
            return jsonify({"success": True})

    return jsonify({"success": False}), 400


@app.route("/clear_cart", methods=["POST"])
@login_required
def clear_cart():
    # Clear the cart from session
    session.pop("cart", None)
    return jsonify({"success": True})


@app.route("/delete_order", methods=["POST"])
@login_required
def delete_order():
    date_str = request.form.get("date")
    if not date_str:
        flash("No date specified")
        return redirect(url_for("dashboard"))

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Find and delete the order
        order = Order.query.filter_by(user_id=current_user.id, date=date).first()

        if order:
            db.session.delete(order)
            db.session.commit()
            flash("Order deleted successfully")
        else:
            flash("No order found for that date")
    except Exception as e:
        logger.error(f"Error deleting order: {e}")
        flash("Error deleting order")
        db.session.rollback()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        # Create all database tables
        db.create_all()

        # Check if any users exist, if not create a default user
        if User.query.count() == 0:
            default_user = User(
                username="admin", password_hash=generate_password_hash("admin")
            )
            db.session.add(default_user)
            db.session.commit()
            print("Created default user: admin/admin")

        app.run(debug=True)
