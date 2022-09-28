from stoploss.collect_data_market import get_ohlc_dataframe, get_indicator_form_ohlc, get_last_trade_price
from stoploss.helper_scripts.helper import get_logger

logger = get_logger("stoploss_logger")


def set_new_trigger(position, std, std_before, high, low, last_trade_price):

    # Sell Position / Trigger below current price / Move trigger up when price rises
    if position.current_volume_of_base_currency > 0:
        logger.debug(f"Calculate Sell Trigger because {position.current_volume_of_base_currency} {position.base_currency} is not 0")
        # Check if there was already a trigger
        if position.trigger > 0:

            # If the old trigger is higher then the new trigger it means the price has fallen. Therefore the trigger should not be moved.
            # The new trigger becomes the old trigger
            new_trigger = high - std_before
            if position.trigger > new_trigger:
                new_trigger = position.trigger

            # If the std is changed the new trigger should be calculated with the changed std
            # if the std got smaller the distance between price and trigger should get smaller
            # if the std got bigger the distance between price and trigger should get bigger
            std_delta = std - std_before
            new_trigger = new_trigger + std_delta

            # Check if the new calculated trigger is below current trade price. if not keep the old trigger
            if new_trigger < last_trade_price:
                # Set trigger below the current high to execute a sell as soon as the price falls
                position.trigger = new_trigger

        elif position.trigger == 0:  # This is the case where it does not has a trigger.
            position.trigger = high - std
            if position.trigger > last_trade_price:
                # Ensure that the new trigger is always below the trading price
                position.trigger = last_trade_price - std
        else:
            raise RuntimeError(f"Position trigger is smaller 0. Value is {position.trigger}")

    # Buy Position / Trigger above current price / Move trigger down when price falls
    else:
        logger.debug(f"Calculate Buy Trigger because {position.current_volume_of_base_currency} {position.base_currency} is equal 0")
        # Check if there was already a trigger
        if position.trigger > 0:

            # If the old trigger is lower then the new trigger it means the price has risen. Therefore the trigger should not be moved.
            # The new trigger becomes the old trigger
            new_trigger = low + std_before
            if position.trigger < new_trigger:
                new_trigger = position.trigger

            # If the std is changed the new trigger should be calculated with the changed std
            # if the std got smaller the distance between price and trigger should get smaller
            # if the std got bigger the distance between price and trigger should get bigger
            std_delta = std - std_before
            new_trigger = new_trigger + std_delta

            # Check if the new calculated trigger is above current trade price. if not keep the old trigger
            if new_trigger > last_trade_price:
                # Set trigger above the current low to execute a buy as soon as the price rises
                position.trigger = new_trigger

        elif position.trigger == 0:  # This is the case where it does not has a trigger.
            position.trigger = low + std
            if position.trigger < last_trade_price:
                # Ensure that the new trigger is always below the trading price
                position.trigger = last_trade_price + std
        else:
            raise RuntimeError(f"Position trigger is smaller 0. Value is {position.trigger}")

    return position


def calculate_stop_loss_trigger(position, order=None, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24):
    # Possible Situations
    # If Order is none: calculate a new trigger based on min or max and the current position
    # If Order is not none: use the existing trigger and calculate a new one

    df_ohlc_minmax = get_ohlc_dataframe(pair=position.exchange_currency_pair, interval=minmax_interval)
    high = get_indicator_form_ohlc(df=df_ohlc_minmax, indicator="max", history_length=minmax_history)
    low = get_indicator_form_ohlc(df=df_ohlc_minmax, indicator="min", history_length=minmax_history)

    # Collect two std's. The current and one period before. This way I can compare if the std has changed.
    df_ohlc_std = get_ohlc_dataframe(pair=position.exchange_currency_pair, interval=std_interval)
    df_ohlc_std_before = df_ohlc_std.iloc[:-1, :]  # Structure: df.iloc[row_start:row_end , col_start, col_end]
    std = get_indicator_form_ohlc(df=df_ohlc_std, indicator="std", history_length=std_history)
    std_before = get_indicator_form_ohlc(df=df_ohlc_std_before, indicator="std", history_length=std_history)

    last_trade_price = get_last_trade_price(position.exchange_currency_pair)

    if order is not None:
        logger.debug(f"There was an order provided. Calculate stop loss trigger based on existing order. Trigger Price was {order.price} {order.quote_currency}")
        position.trigger = order.price

    position = set_new_trigger(position, std, std_before, high, low, last_trade_price)

    print(f"\n"
          f"Standard Deviation: {std} / High Price: {high} {position.quote_currency} / Low Price: {low} {position.quote_currency} / Last Trade Price: {last_trade_price}\n"
          f"Current Trigger: {position.trigger} {position.quote_currency}")

    return position
