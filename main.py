# Execute this main to start the trader. Feel free to just execute trade_stoploss via python console using:
# python trade_stoploss.py

from subprocess import call
from stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

log_level = cfg["debugging"]["log-level"]
file_log_level = cfg["debugging"]["file_log_level"]

logger = get_logger("main_logger", log_level)

if __name__ == "__main__":

    call(["python", "trade_stoploss.py", "--trading_time", "2023-12-31T00:00:00+0200", "--log_level", log_level, "--secret_type", "local"])

    logger.info("Program Executed")


