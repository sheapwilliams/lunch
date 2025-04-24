from app import app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

application = app

if __name__ == "__main__":
    application.run()
