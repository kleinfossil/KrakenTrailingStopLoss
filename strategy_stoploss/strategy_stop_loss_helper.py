# Additional Helper Scripts not directly related to the stop loss trigger calculation

import traceback
from decimal import Decimal
from strategy_stoploss.collect_data_user import get_account_balance_per_currency
from strategy_stoploss.helper_scripts.helper import (
    get_logger)
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def get_interval_as_int(interval):
    # Transforms the intervals provided into integer numbers.
    try:
        match interval:
            case "w":
                interval_int = 10080
            case "d":
                interval_int = 1440
            case "h":
                interval_int = 60
            case "m":
                interval_int = 1
            case _:
                raise ValueError(f"{interval} is not a valid period. Choose 'd' for days, 'h' for hours, 'm' for minutes")
        return interval_int
    except ValueError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def get_buy_or_sell_type(position):
    # Returns an information of a traders position is buy or sell
    # This is a hardcoded method which could be refined in future.

    if position.current_volume_of_base_currency == 0:
        logger.debug("Base Currency is equal 0. Therefore execute BUY trade.")
        buy_sell = "buy"
    elif position.current_volume_of_base_currency > 0:
        logger.debug("Base Currency is bigger 0. Therefore execute SELL trade.")
        buy_sell = "sell"
    else:
        raise RuntimeError(f"{position.current_volume_of_base_currency} {position.base_curency} is below 0")
    return buy_sell


def get_limit_price_and_volume(position, buy_sell_type):
    # It finds a limit price based on the offset setup in the config.

    trade_dict = {"volume": 0, "price": 0}
    account_balance = get_account_balance_per_currency(position.exchange_currency_pair)
    if buy_sell_type == "sell":
        trade_dict["price"] = position.trigger - Decimal(cfg["trading"]["strategy"]["stop_loss"]["sell_price_offset"])
        trade_dict["volume"] = Decimal(account_balance[position.base_currency])

    elif buy_sell_type == "buy":
        trade_dict["price"] = position.trigger + Decimal(cfg["trading"]["strategy"]["stop_loss"]["buy_price_offset"])
        max_quote_currency = Decimal(account_balance[position.quote_currency]) - Decimal(cfg["trading"]["strategy"]["stop_loss"]["quote_currency_offset"])
        trade_dict["volume"] = max_quote_currency/ trade_dict["price"]
    else:
        raise RuntimeError(f"{buy_sell_type} is not a valid buy or sell type. Must by 'buy' or 'sell'")

    logger.debug(f"Executing simple limit strategy. Trigger is {position.trigger} {position.quote_currency}. Limit Price is {trade_dict['price']} {position.quote_currency}")
    return trade_dict


def get_stop_trigger(position):
    # Just returns the stop loss trigger

    return position.trigger




