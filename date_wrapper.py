import calendar
import time
from datetime import datetime, timedelta

def get_current_time_stamp():
    '''Get current system time stamp'''
    return calendar.timegm(time.gmtime())


def is_within_last_3_minutes(timestamp_str):
    """Check if a timestamp is within the last 3 minutes from current time."""
    patterns = ["%I:%M %p", "%H:%M"]
    for pattern in patterns:
        try:
            time_obj = datetime.strptime(timestamp_str.strip(), pattern).time()
            input_time = datetime.combine(datetime.today().date(), time_obj)
            time_diff = datetime.now() - input_time
            return 0 <= time_diff.total_seconds() <= 180
        except ValueError:
            continue
    return False
