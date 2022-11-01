import os
import shutil
from strategy_stoploss.helper_scripts.helper import get_logger
logger = get_logger("backtest_logger")


def clean_backtest_runtime_data():
    folder = '/strategy_stoploss/backtest/runtime_data'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error('Failed to delete %s. Reason: %s' % (file_path, e))
