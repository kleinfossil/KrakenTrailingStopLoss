import traceback
import time
from stoploss.data_classes.StopLoss_Trigger import StopLoss_Trigger

from stoploss.collect_data_market import get_last_trade_price
from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level, convert_unix_time_to_datetime)
logger = get_logger("stoploss_logger", "INFO")

def get_interval_as_int(interval):
    try:
        match interval:
            case "d": interval_int = 1440
            case "h": interval_int = 60
            case "m": interval_int = 1
            case _: raise ValueError(f"{interval} is not a valid period. Choose 'd' for days, 'h' for hours, 'm' for minutes")
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
    sleep_time = repeat_time/10
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





