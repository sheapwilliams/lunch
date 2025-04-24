import logging
import os
from models import db

# Configure logging
logger = logging.getLogger(__name__)

def init_db(app):
    """Initialize the database, create tables if they don't exist"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Existing tables: {tables}")
            
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

        # Create database file if it doesn't exist
        db_path = os.path.join(instance_path, "lunch.db")
        if not os.path.exists(db_path):
            os.close(os.open(db_path, os.O_CREAT))
            os.chmod(db_path, 0o666)  # Read/write for all users
            logger.info(f"Created database file at {db_path}")

        # Ensure the database file has the correct permissions
        os.chmod(db_path, 0o666)
        logger.info("Set database file permissions to 0o666")

        # Log paths for debugging
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Database path: {db_path}")
        logger.info(f"Database path exists: {os.path.exists(db_path)}")
        logger.info(f"Database path is absolute: {os.path.isabs(db_path)}")

        # Configure SQLAlchemy
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        
        # Initialize the db with the app
        db.init_app(app)
        
        # Create tables
        init_db(app)
        
        return DATA_DIR
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise 