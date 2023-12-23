from datetime import datetime
import time

# create a new function that takes in a datetime.datetime object and returns an integer date

def format_datetime(dt: datetime):
    """
    Formats a datetime object into an integer date.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    # Convert to Unix timestamp in milliseconds
    unix_timestamp = int(dt.timestamp() * 1000)
    return unix_timestamp

def export_datetime(dt):
    """
    Exports a datetime object to a string in ISO 8601 format with a Zulu timezone.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def parse_created_at(createdAt):
    """
    Parses the 'createdAt' parameter into a datetime object.
    Accepts either a float (representing a Unix timestamp) or a string (ISO 8601 format).
    """
    print(f"Type of createdAt: {type(createdAt)}")
    if createdAt is None:
        return None

    if isinstance(createdAt, float):
        return datetime.fromtimestamp(createdAt)
    elif isinstance(createdAt, str):
        if createdAt.endswith('Z'):
            createdAt = createdAt.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(createdAt)
        except ValueError:
            raise ValueError("Invalid date format for 'createdAt'. Expected ISO 8601 format.")
    else:
        raise ValueError("Invalid type for 'createdAt'. Expected float or string.")


def log_function_call(function_name: str, **kwargs):
    print(f"\n{function_name} called with parameters:")
    for key, value in kwargs.items():
        print(f"\t{key}: {value} (type: {type(value)})")
    print("\n" + "-" * 50)  