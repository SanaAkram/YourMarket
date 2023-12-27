from datetime import datetime, date, timedelta
import pytz
import numpy as np
import ctypes
import base64
from yourmarket.helpers import return_400


def auth_check(self):
    hash_code = None
    if 'HTTP_X_HASH' in self.request.META:
        hash_code = self.request.META.get('HTTP_X_HASH')
    if hash_code != getHash() and hash_code != getHash(-1) and hash_code != getHash(1) and hash_code != getHash(
            -2) and hash_code != getHash(-3):
        return_400('Authentication credentials were not provided.', 400)


def getHash(minute=0):
    today = datetime.utcnow()
    date_string = '{} {} {} {} {}:{} - www.lineups.com'.format(today.strftime("%a"), today.strftime("%b"),
                                                               "{:02d}".format(today.day), today.year,
                                                               np.uint32(today.strftime("%H")),
                                                               addRemoveMinute(today.strftime("%M"), minute))
    # print(date_string)
    return base64.b64encode(hashCode(date_string).encode("utf-8")).decode('utf-8')


def hashCode(temp):
    hash_ = np.uint32(0);
    if len(temp) == 0:
        return str(hash_)
    for i, char in enumerate(temp):
        hash_ = ((ctypes.c_int(hash_ << 5 ^ 0).value) - hash_) + ord(char)
        hash_ = ctypes.c_int(hash_ & hash_).value

    return str(hash_)


def addRemoveMinute(minutes, minute):
    intMins = np.uint32(minutes)
    resMins = intMins + minute
    if resMins < 0:
        resMins = 60
    elif resMins > 60:
        resMins = 0
    return resMins

# past minute
# print(getHash(-1))
# # current minute
# print(getHash())
# # future minute
# print(getHash(1))
