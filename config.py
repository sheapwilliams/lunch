import pytz
from datetime import time

# Location Configuration
LOCATION = {
    "name": "Denver",
    "timezone": "America/Denver",  # Uses pytz timezone format
    "ordering_cutoff": time(hour=10, minute=30),  # 11:00 AM local time
    "display_name": "Aspen, CO",
    "icon": "cppnow-logo.png",  # Custom logo image
}


# Helper function to get the configured timezone
def get_timezone():
    return pytz.timezone(LOCATION["timezone"])


# Helper function to get the cutoff time
def get_cutoff_time():
    return LOCATION["ordering_cutoff"]
