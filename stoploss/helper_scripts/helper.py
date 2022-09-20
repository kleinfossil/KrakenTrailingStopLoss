# Script functions which are generic and not specific to this project
import math
import datetime
import logging

from stoploss.helper_scripts.formated_logger import CustomFormatter


# Take a unix time stamp and return a data and time format
def convert_unix_time_of_dateframe(unix_time):
    date_and_time = datetime.datetime.fromtimestamp(unix_time)
    return str(date_and_time)


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
def get_logger(name="log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger
