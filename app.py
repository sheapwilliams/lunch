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
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import logging
from config import get_timezone, get_cutoff_time, LOCATION
import pytz

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lunch.db"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.getcwd(), "flask_session")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# Add datetimeformat filter
@app.template_filter("datetimeformat")
def datetimeformat(value):
    try:
        date = datetime.strptime(value, "%Y-%m-%d")
        return date.strftime("%A, %B %d")
    except ValueError:
        return value


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
Session(app)


# Initialize session for new users
@app.before_request
def before_request():
    # Initialize session for new users and ensure cart is user-specific
    if current_user.is_authenticated:
        if "cart" not in session:
            session["cart"] = {}
        # Ensure the cart belongs to the current user
        if "user_id" not in session or session["user_id"] != current_user.id:
            session["cart"] = {}
            session["user_id"] = current_user.id
        session.permanent = True
        session.modified = True


# Helper function to check if ordering is closed for a date
def is_ordering_closed(date):
    # Get current time in UTC
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)

    # Get the cutoff time in configured timezone and convert to UTC
    tz = get_timezone()
    cutoff_local = get_cutoff_time()
    # Create a datetime with the input date and cutoff time in local timezone
    cutoff_local_dt = tz.localize(datetime.combine(date, cutoff_local))
    # Convert cutoff time to UTC
    cutoff_utc = cutoff_local_dt.astimezone(pytz.UTC)

    # Convert the input date to UTC for comparison
    date_local = tz.localize(datetime.combine(date, datetime.min.time()))
    date_utc = date_local.astimezone(pytz.UTC)

    # Convert all to Unix timestamps
    now_ts = now_utc.timestamp()
    cutoff_ts = cutoff_utc.timestamp()
    date_ts = date_utc.timestamp()

    # Debug logging
    app.logger.debug(f"Checking ordering status for date: {date}")
    app.logger.debug(f"Current time (UTC): {now_utc}")
    app.logger.debug(f"Cutoff time (UTC): {cutoff_utc}")
    app.logger.debug(f"Date in UTC: {date_utc}")
    app.logger.debug(
        f"Unix timestamps - now: {now_ts}, cutoff: {cutoff_ts}, date: {date_ts}"
    )

    # If we're past the cutoff time for this date
    if now_ts >= cutoff_ts:
        app.logger.debug("Ordering is closed for this date")
        return True
    app.logger.debug("Ordering is open for this date")
    return False


# Load lunch options from JSON file
def load_lunch_options():
    with open("data/lunch_options.json", "r") as f:
        data = json.load(f)
        return data["daily_options"]


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
    meal_name = db.Column(
        db.String(100), nullable=False
    )  # Changed from meal_type to meal_name


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html", location=LOCATION)


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
    return render_template("login.html", location=LOCATION)


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
    return render_template("register.html", location=LOCATION)


@app.route("/dashboard")
@login_required
def dashboard():
    # Load lunch options first
    lunch_options = load_lunch_options()

    # Get dates from lunch options
    week_dates = sorted(lunch_options.keys())

    # Get user's orders
    orders = Order.query.filter_by(user_id=current_user.id).all()
    # Convert orders to a serializable format
    orders_dict = {}
    for order in orders:
        date_str = order.date.strftime("%Y-%m-%d")
        orders_dict[date_str] = order.meal_name

    # Get cart from session
    cart = session.get("cart", {})

    # Check which dates have ordering closed
    ordering_closed = {}
    for date_str in week_dates:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        ordering_closed[date_str] = is_ordering_closed(date)

    # Debug logging
    app.logger.debug(f"Week dates: {week_dates}")
    app.logger.debug(f"Lunch options: {lunch_options}")
    app.logger.debug(f"Orders: {orders_dict}")
    app.logger.debug(f"Cart: {cart}")
    app.logger.debug(f"Ordering closed: {ordering_closed}")

    template_vars = {
        "week_dates": week_dates,
        "lunch_options": lunch_options,
        "orders": orders_dict,
        "cart": cart,
        "ordering_closed": ordering_closed,
        "location": LOCATION,
    }

    return render_template("dashboard.html", **template_vars)


@app.route("/order", methods=["POST"])
@login_required
def order():
    logger.debug(f"Received order request: {request.form}")

    # Load lunch options to get meal names
    lunch_options = load_lunch_options()

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

            # Find the meal name for this meal type
            meal_name = "None"
            if date_str in lunch_options:
                for meal in lunch_options[date_str]["meals"]:
                    if meal["type"] == meal_type:
                        meal_name = meal["name"]
                        break

            logger.debug(f"Processing order for date: {date}, meal_name: {meal_name}")

            # Check if order already exists for this date
            existing_order = Order.query.filter_by(
                user_id=current_user.id, date=date
            ).first()

            if existing_order:
                logger.debug(f"Updating existing order: {existing_order}")
                existing_order.meal_name = meal_name
            else:
                logger.debug("Creating new order")
                new_order = Order(
                    user_id=current_user.id, date=date, meal_name=meal_name
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
    # Clear all session data
    session.clear()
    logout_user()
    return redirect(url_for("index"))


@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    try:
        logger.debug(f"Current user: {current_user.username}")
        logger.debug(f"Session before update: {session}")
        logger.debug(f"Form data received: {request.form}")

        # Load lunch options to get meal names
        lunch_options = load_lunch_options()

        # Get the cart from session or initialize it
        cart = session.get("cart", {})
        logger.debug(f"Current cart: {cart}")

        # Track removed items for the flash message
        removed_items = []

        # Process all selections in the form
        for key, meal_type in request.form.items():
            if key.startswith("meal_type_"):
                date_str = key.replace("meal_type_", "")
                logger.debug(
                    f"Processing selection - date: {date_str}, meal_type: {meal_type}"
                )

                # Skip empty selections
                if not meal_type or meal_type.strip() == "":
                    logger.debug(f"Skipping empty selection for date: {date_str}")
                    continue

                # Handle None selection
                if meal_type == "N":
                    logger.debug(f"Handling None selection for date: {date_str}")
                    if date_str in cart:
                        del cart[date_str]
                    continue

                # Check if ordering is closed for this date
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if is_ordering_closed(date):
                    removed_items.append(date_str)
                    continue

                # Find the meal name for this meal type
                meal_name = "None"
                if date_str in lunch_options:
                    for meal in lunch_options[date_str]["meals"]:
                        if meal["type"] == meal_type:
                            meal_name = meal["name"]
                            break

                # Add valid meal selection to cart
                cart[date_str] = meal_name
                logger.debug(f"Added to cart - date: {date_str}, meal: {meal_name}")

        # Save the cart to session without clearing other session data
        session["cart"] = cart
        session["user_id"] = current_user.id
        session.modified = True
        logger.debug(f"Updated cart: {cart}")
        logger.debug(f"Session after update: {session}")

        # Add flash message if any items were removed
        if removed_items:
            flash(
                f"Some items were removed because ordering was closed: {', '.join(removed_items)}",
                "warning",
            )

        # Only show success message if there are items in the cart
        if cart:
            flash("Items added to cart!")

        return redirect(url_for("cart"))
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}")
        flash("Error adding items to cart. Please try again.")
        return redirect(url_for("dashboard"))


@app.route("/submit_cart", methods=["POST"])
@login_required
def submit_cart():
    cart = session.get("cart", {})

    # Process all orders in the cart
    for date_str, meal_name in cart.items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check if order already exists for this date
        existing_order = Order.query.filter_by(
            user_id=current_user.id, date=date
        ).first()

        if existing_order:
            existing_order.meal_name = meal_name
        else:
            new_order = Order(user_id=current_user.id, date=date, meal_name=meal_name)
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
    try:
        session.pop("cart", None)
        session["cart"] = {}  # Reinitialize empty cart
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return jsonify({"success": False}), 500


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


@app.route("/cart")
@login_required
def cart():
    lunch_options = load_lunch_options()
    return render_template(
        "cart.html",
        cart=session.get("cart", {}),
        lunch_options_json=lunch_options,
        location=LOCATION,
    )


if __name__ == "__main__":
    with app.app_context():
        # Create all database tables
        db.create_all()
        app.run(debug=True)
