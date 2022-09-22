# Script functions which are generic and not specific to this project
import math
import datetime
import time
import logging

from stoploss.helper_scripts.formated_logger import CustomFormatter


# Take a unix time stamp and return a data and time format
def convert_unix_time_to_datetime(unix_time):
    date_and_time = datetime.datetime.fromtimestamp(unix_time)
    return str(date_and_time)


def convert_datetime_to_unix_time(date_time):
    d = datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z')
    unix_time = time.mktime(d.timetuple())
    return unix_time


# Calculate variance based on a list of data
def get_variance(data, degree_of_freedom=0):
    n = len(data)
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / (n - degree_of_freedom)


# Calculate standard deviation based on a list of data
def get_stdev(data):
    var = get_variance(data)
    std_dev = math.sqrt(var)
    return std_dev


# Creates a colorful logger
def get_logger(name="log", log_level="DEBUG"):

    logger = logging.getLogger(name)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    set_log_level(logger, log_level)
    set_log_level(ch, log_level)

    ch.setFormatter(CustomFormatter())
    if not logger.handlers:
        logger.addHandler(ch)
    return logger


def set_log_level(logger, log_level):
    match log_level.upper():
        case "NOTSET":
            logger.setLevel(logging.NOTSET)
        case "DEBUG":
            logger.setLevel(logging.DEBUG)
        case "INFO":
            logger.setLevel(logging.INFO)
        case "WARNING":
            logger.setLevel(logging.WARNING)
        case "ERROR":
            logger.setLevel(logging.ERROR)
        case "CRITICAL":
            logger.setLevel(logging.CRITICAL)
    return logger
