import traceback
import time
from decimal import Decimal

from stoploss.collect_data_user import get_account_balance_per_currency
from stoploss.data_classes.StopLoss_Trigger import StopLoss_Trigger

from stoploss.helper_scripts.helper import (
    get_logger,
    convert_unix_time_to_datetime)

import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def get_interval_as_int(interval):
    try:
        match interval:
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


def initiate_stop_loss_trigger(position, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24):
    stdi = get_interval_as_int(std_interval)
    mmi = get_interval_as_int(minmax_interval)
    try:
        if position.trigger == 0:
            # Create initial trigger
            stop_loss_position = StopLoss_Trigger(position=position, std_interval=stdi, std_history=std_history, minmax_interval=mmi, minmax_history=minmax_history)
            stop_loss_position.position.add_to_position_book(book_time=time.time(), last_low=stop_loss_position.last_low, last_high=stop_loss_position.last_high, last_std=stop_loss_position.last_std, last_trade_price=stop_loss_position.last_trade_price)
        else:
            raise RuntimeError(f"Position Trigger is not 0. You tried to execute the initiation of a stop_loss trigger with an active position. Try update instead.")
        return stop_loss_position
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def update_stop_loss_trigger(stop_loss_position, repeat_time, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24):
    stdi = get_interval_as_int(std_interval)
    mmi = get_interval_as_int(minmax_interval)
    next_execution_time = stop_loss_position.get_last_execution_time() + repeat_time
    current_time = time.time()
    sleep_time = repeat_time / 10
    print(f"It is now: {convert_unix_time_to_datetime(current_time)}. Next execution starts at {convert_unix_time_to_datetime(next_execution_time)}.")
    while current_time < next_execution_time:
        print(f"Sleep {sleep_time}")
        time.sleep(sleep_time)
        current_time = time.time()
    try:
        if stop_loss_position.position.trigger > 0:
            # Update trigger
            stop_loss_position.calculate_trigger(std_interval=stdi, std_history=std_history, minmax_interval=mmi, minmax_history=minmax_history)
            stop_loss_position.position.add_to_position_book(book_time=time.time(), last_low=stop_loss_position.last_low, last_high=stop_loss_position.last_high, last_std=stop_loss_position.last_std, last_trade_price=stop_loss_position.last_trade_price)
        else:
            raise RuntimeError(f"Position Trigger is not larger 0 (value is {stop_loss_position.position.trigger}. You tried to execute the update of a stop_loss trigger with an active position. Try initiate instead.")
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def get_buy_or_sell_type(position):
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
    return position.trigger




