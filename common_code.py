from datetime import datetime
import random
import string
import pytz


def get_ist(return_dt_obj=False):
    tz = pytz.timezone('Asia/Kolkata')
    chennai_now = datetime.now(tz)
    if return_dt_obj:
        return chennai_now
    return chennai_now.strftime("%d/%m/%Y %H:%M:%S")


def get_random(length=12):
    return ''.join(random.choices(
        string.ascii_uppercase +
        string.ascii_lowercase +
        string.digits,
        k=length
    ))
