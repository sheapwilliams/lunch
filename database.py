import logging
import os
import fcntl
from models import db
from sqlalchemy import inspect

# Configure logging
logger = logging.getLogger(__name__)


def tables_exist(app):
    """Check if all required tables exist"""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = {"users", "orders"}
        return required_tables.issubset(existing_tables)


def init_db(app):
    """Initialize the database, create tables if they don't exist"""
    try:
        with app.app_context():
            if tables_exist(app):
                logger.info("Required tables already exist")
                return True

            db.create_all()
            logger.info("Database tables created successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def setup_db(app):
    """Setup database configuration and initialize it"""
    try:
        # Get data directory
        if os.environ.get("DATA_DIR"):
            DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR"))
        else:
            DATA_DIR = os.path.abspath(os.path.dirname(__file__))
        logger.info(f"Using data directory: {DATA_DIR}")

        # Create instance directory if it doesn't exist
        instance_path = os.path.join(DATA_DIR, "instance")
        if not os.path.exists(instance_path):
            os.makedirs(instance_path, mode=0o755)
            logger.info(f"Created instance directory at {instance_path}")

        # Create lock file path
        lock_path = os.path.join(instance_path, "db.lock")

        # Acquire lock for database initialization
        with open(lock_path, "w") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                logger.debug("Acquired database initialization lock")

                # Create database file if it doesn't exist
                db_path = os.path.join(instance_path, "lunch.db")
                if not os.path.exists(db_path):
                    os.close(os.open(db_path, os.O_CREAT))
                    os.chmod(db_path, 0o666)
                    logger.info(f"Created database file at {db_path}")
                else:
                    logger.info(f"Database file already exists at {db_path}")

                # Configure SQLAlchemy
                app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

                # Initialize the db with the app
                db.init_app(app)

                # Initialize tables if needed
                init_db(app)

                return DATA_DIR

            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                logger.debug("Released database initialization lock")

    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise
