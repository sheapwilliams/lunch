import pytz
from datetime import time

# Location Configuration
LOCATION = {
    "name": "Denver",
    "timezone": "America/Denver",  # Uses pytz timezone format
    "ordering_cutoff": time(hour=9, minute=30),  # 9:30 AM local time
    "display_name": "Aspen, CO",
}


# Helper function to get the configured timezone
def get_timezone():
    return pytz.timezone(LOCATION["timezone"])


# Helper function to get the cutoff time
def get_cutoff_time():
    return LOCATION["ordering_cutoff"]
