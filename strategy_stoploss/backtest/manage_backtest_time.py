import pickle
import traceback

from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader


with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    backtest_cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")


def get_backtest_start_time_unix(backtest_status):
    return int(backtest_cfg["backtest"]["timeframe"])


def get_current_backtest_time_unix():
    try:
        with open('strategy_stoploss/backtest/runtime_data/backtest_current_time.pickle', 'rb') as f:
            return int(pickle.load(f))
    except FileNotFoundError as e:
        logger.error(traceback, e)
        exit(1)


def set_backtest_starting_time(backtest_status):
    if backtest_status == 1:
        logger.debug("Backtest is active")
        backtest_starting_time = get_backtest_start_time_unix(backtest_status)
        try:
            with open('strategy_stoploss/backtest/runtime_data/backtest_current_time.pickle', 'wb') as f:
                pickle.dump(backtest_starting_time, f)
            return backtest_starting_time
        except FileNotFoundError as e:
            logger.error(traceback, e)
            exit(1)
    elif backtest_status == 0:
        logger.debug("Backtest is inactive")
    else:
        raise RuntimeError(f"Backtest is not configured correctly. Should be '1' or '0' but is {backtest_status}")


def set_backtest_forward():
    next_check_in_sec = int(cfg["trading"]["waiting_time"])
    new_backtest_time = get_current_backtest_time_unix() + next_check_in_sec
    try:
        with open('strategy_stoploss/backtest/runtime_data/backtest_current_time.pickle', 'wb') as f:
            pickle.dump(new_backtest_time, f)
            return new_backtest_time
    except FileNotFoundError as e:
        logger.error(traceback, e)
        exit(1)


def set_backtest_time(backtest_time):
    new_backtest_time = backtest_time
    try:
        with open('strategy_stoploss/backtest/runtime_data/backtest_current_time.pickle', 'wb') as f:
            pickle.dump(new_backtest_time, f)
    except FileNotFoundError as e:
        logger.error(traceback, e)
        exit(1)
