import traceback
import time
from stoploss.data_classes.StopLoss_Trigger import StopLoss_Trigger

from stoploss.collect_data_market import get_last_trade_price
from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level)
logger = get_logger("stoploss_logger")

def get_interval_as_int(interval):
    try:
        match interval:
            case "d": interval_int = 1440,
            case "h": interval_int = 60,
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
            active_stop_loss = StopLoss_Trigger(position=position, std_interval=stdi, std_history=std_history, minmax_interval=mmi, minmax_history=minmax_history)
        else:
            raise RuntimeError(f"Position Trigger is not 0. You tried to execute the initiation of a stop_loss trigger with an active position. Try update instead.")
        return active_stop_loss
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def update_stop_loss_trigger(stop_loss_position, repeat_time, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24):
    stdi = get_interval_as_int(std_interval)
    mmi = get_interval_as_int(minmax_interval)
    next_execution_time = stop_loss_position.get_last_execution_time() + repeat_time
    current_time = time.time()
    sleep_time = repeat_time/10
    while current_time > next_execution_time:
        print(f"It is now: {current_time}. Execution Starts at {next_execution_time}. Sleep {sleep_time}")
        time.sleep(sleep_time)
        current_time = time.time()
    try:
        if stop_loss_position.position.trigger > 0:
            # Update trigger
            active_stop_loss = StopLoss_Trigger(position=stop_loss_position, std_interval=stdi, std_history=std_history, minmax_interval=mmi, minmax_history=minmax_history)
        else:
            raise RuntimeError(f"Position Trigger is not larger 0 (value is {stop_loss_position.position.trigger}. You tried to execute the update of a stop_loss trigger with an active position. Try initiate instead.")
        return active_stop_loss
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")
    return stop_loss_position




