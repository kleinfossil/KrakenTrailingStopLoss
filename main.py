# Execute this main to start the trader. Feel free to just execute trade_stoploss via python console using:
# python trade_stoploss.py

from subprocess import call
from stoploss.helper_scripts.helper import get_logger

log_level = "DEBUG"

logger = get_logger("main_logger", log_level)


if __name__ == "__main__":
    # simple_test()
    call(["python", "trade_stoploss.py", "--std_history", "10", "--minmax_history", "24", "--log_level", log_level])

    logger.debug("Program Executed")
    logger.info("Program Executed")
    logger.warning("Program Executed")
    logger.error("Program Executed")
    logger.critical("Program Executed")

