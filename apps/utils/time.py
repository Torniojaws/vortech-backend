import time


def get_datetime():
    """Return the current datetime in a database compatible format"""
    return time.strftime('%Y-%m-%d %H:%M:%S')
