import traceback

from stoploss.collect_data_market import get_last_trade_price
from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level)
logger = get_logger("stoploss_logger")


def set_sell_trigger(position, std_interval, std_history, minmax_interval, minmax_history):
    try:
        match std_interval:
            case "d": interval = 1440,
            case "h": interval = 60,
            case "m": interval = 1
            case _: raise ValueError(f"{std_interval} is not a valid period. Choose 'd' for days, 'h' for hours, 'm' for minutes")

    except ValueError as e:
        logger.error(f"{traceback.print_stack()} {e}")

    market_price = get_last_trade_price(position.exchange_currency_pair)
    print(f"Current Market Price: {market_price}")



    return position