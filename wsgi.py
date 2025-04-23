from app import app, db
from dotenv import load_dotenv
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def configure_app(data_dir):
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Ensure instance directory exists under data_dir
    instance_path = os.path.join(data_dir, "instance")
    os.makedirs(instance_path, exist_ok=True)

    # Configure application paths
    db_path = os.path.join(instance_path, "lunch.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SESSION_FILE_DIR"] = os.path.join(data_dir, "flask_session")
    app.config["DATA_DIR"] = data_dir  # Store for other uses (like lunch_options.json)

    # Initialize database if it doesn't exist or is empty
    with app.app_context():
        try:
            # Try to query a table we know should exist
            db.session.execute(text("SELECT * FROM user LIMIT 1"))
            app.logger.info("Database already initialized")
        except OperationalError as e:
            if "no such table" in str(e):
                # Create all tables
                db.create_all()
                app.logger.info(f"Initialized empty database at {db_path}")
            else:
                # Re-raise if it's a different database error
                raise

    return app


# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Configure using DATA_DIR environment variable
data_dir = os.environ.get("DATA_DIR", ".")
application = configure_app(os.path.abspath(data_dir))

if __name__ == "__main__":
    application.run()
