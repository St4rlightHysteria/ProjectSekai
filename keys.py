from datetime import datetime
from dateutil import tz

def parse_datetime(datetime_str):
    ZaWarudo = None
    try:
        ZaWarudo = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            ZaWarudo = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return ZaWarudo


def convert_to_utc(local_time_str, local_timezone_str):
    """
    Convert a local time to UTC time based on the local timezone.

    Args:
    - local_time_str (str): Local time string (format: "YYYY-MM-DD HH:MM:SS").
    - local_timezone_str (str): Local timezone string (e.g., "Europe/Amsterdam", "Asia/Tokyo").

    Returns:
    - str: UTC time string in "YYYY-MM-DD HH:MM:SS" format.
    """
    # Parse the local time string into a datetime object
    local_time = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")

    # Get the local timezone object
    local_tz = tz.gettz(local_timezone_str)

    # Attach the local timezone to the local time
    local_time = local_time.replace(tzinfo=local_tz)

    # Convert the localized time to UTC
    utc_time = local_time.astimezone(tz.UTC)

    # Format the UTC datetime as a string without the "+00:00"
    utc_time_str = utc_time.strftime("%Y-%m-%d %H:%M:%S")

    return parse_datetime(utc_time_str)

SECRET_KEY = "4db4f4a47a422634322c5728da0281650c2d7be4c3467d41"
EMAIL_PASSWORD = "ehnv zioo ciin thsd"

utc_time = convert_to_utc("2024-02-17 00:00:00", "Europe/Amsterdam")
print(utc_time)
