# Script functions which are generic and not specific to this project
import math
import datetime
import pickle
import time
import logging
import traceback

from tqdm import tqdm
from strategy_stoploss.helper_scripts.formated_logger import CustomFormatter
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def convert_unix_time_to_datetime(unix_time):
    # Take a unix time stamp and return a data and time format
    date_and_time = datetime.datetime.fromtimestamp(unix_time)
    return str(date_and_time)


def convert_datetime_to_unix_time(date_time, time_format="%Y-%m-%dT%H:%M:%S%z"):
    # Converts datetime to a unix time stamp
    d = datetime.datetime.strptime(date_time, time_format)
    unix_time = time.mktime(d.timetuple())
    return unix_time


def get_variance(data, degree_of_freedom=0):
    # Calculate variance based on a list of data
    n = len(data)
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / (n - degree_of_freedom)


def get_stdev(data):
    # Calculate standard deviation based on a list of data
    var = get_variance(data)
    std_dev = math.sqrt(var)
    return std_dev


def get_logger(name="log", log_level="DEBUG"):
    # Creates a colorful logger

    logger = logging.getLogger(name)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    today = datetime.date.today()
    d = today.strftime("%Y%m%d")
    try:
        from pathlib import Path
        Path(cfg['basic']['logs-location']).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"{traceback.print_stack()} {e} \n Could not create path for logs. Check configuration")
        exit(1)
    fh = logging.FileHandler(f'{cfg["basic"]["logs-location"]}{d}_kraken_log.log')
    set_log_level(logger, log_level)
    set_log_level(ch, log_level)
    set_log_level(fh, cfg["debugging"]["file_log_level"])

    ch.setFormatter(CustomFormatter())

    simple_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)")
    fh.setFormatter(simple_formatter)
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)
    return logger


def set_log_level(logger, log_level):
    # Ensures that the log level provided is one of the log levels supported
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


def pretty_waiting_time(waiting_time):
    # Creates a pretty waiting time. This can be sometimes messed up and create errors. Therefore you can deactivate it in the trader_config.yml
    for i in tqdm(range(1, waiting_time)):
        time.sleep(1)


