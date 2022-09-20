# Execute this main to start the trader. Feel free to just execute trade_stoploss via python console using:
# python trade_stoploss.py

from subprocess import call
from stoploss.helper_scripts.helper import get_logger

logger = get_logger("main_logger")


if __name__ == "__main__":
    # simple_test()
    call(["python", "trade_stoploss.py", "--std_history", "15", "--minmax_history", "24"])

    logger.info("Program Executed")

