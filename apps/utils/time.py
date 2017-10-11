from datetime import datetime, timedelta
import time


def get_datetime():
    """Return the current datetime in a database compatible format"""
    return time.strftime('%Y-%m-%d %H:%M:%S')


def get_date():
    """Return the current date in Date format."""
    return time.strftime('%Y-%m-%d')


def get_monday():
    """Return the date of current week's Monday in datetime format."""
    now = datetime.now()
    return (now - timedelta(days=now.weekday()) + timedelta(days=0)).strftime("%Y-%m-%d 00:00:00")


def get_first_day():
    """Return the datetime of current month's first day."""
    now = datetime.now()
    return datetime(now.year, now.month, 1).strftime("%Y-%m-%d 00:00:00")


def get_iso_format(date):
    """Convert the date (normally a DateTime object from DB) to ISO format YYYY-MM-DD HH:MM:SS."""
    return date.strftime('%Y-%m-%d %H:%M:%S')
