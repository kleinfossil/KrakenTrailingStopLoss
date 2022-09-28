from stoploss.collect_data_market import get_ohlc_dataframe, get_indicator_form_ohlc, get_last_trade_price
from stoploss.helper_scripts.helper import get_logger
from stoploss.strategy_stop_loss import get_interval_as_int
from decimal import Decimal

logger = get_logger("stoploss_logger")


def set_new_trigger(position, std, std_before, high, low, last_trade_price):
    # Ensure that the data type is Decimal and not float
    new_trigger: Decimal
    std_delta: Decimal
    std = Decimal(str(std))
    std_before = Decimal(str(std_before))
    high = Decimal(str(high))
    low = Decimal(str(low))
    last_trade_price = Decimal(str(last_trade_price))
    # If the std is changed the new trigger should be calculated with the changed std
    # if the std got smaller the distance between price and trigger should get smaller
    # if the std got bigger the distance between price and trigger should get bigger
    std_delta = std - std_before
    logger.debug(f"{std_delta=} = {std=} - {std_before=}")

    # Sell Position / Trigger below current price / Move trigger up when price rises
    if position.current_volume_of_base_currency > 0:
        logger.debug(f"Calculate Sell Trigger because {position.current_volume_of_base_currency} {position.base_currency} is not 0")
        # Check if there was already a trigger
        if position.trigger > 0:
            logger.debug(f"{position.trigger=} > 0. Therefore old order")

            # If the old trigger is higher then the new trigger it means the price has fallen. Therefore the trigger should not be moved.
            # The new trigger becomes the old trigger
            new_trigger = high - std_before
            if position.trigger > new_trigger:
                new_trigger = position.trigger

            logger.debug(f"Sell Trigger before adding {std_delta=}: {new_trigger=}")
            new_trigger = new_trigger + std_delta
            logger.debug(f"Sell Trigger after adding {std_delta=}: {new_trigger=}")

            # Check if the new calculated trigger is below current trade price. if not keep the old trigger
            if new_trigger < last_trade_price:
                # Set trigger below the current high to execute a sell as soon as the price falls
                logger.debug(f"Trigger was smaller then {last_trade_price=}. As this sell, position trigger will be set to {new_trigger=}")
                position.trigger = new_trigger
            else:
                logger.debug((f"Trigger was bigger then {last_trade_price=}. As this is a sell, position trigger will stay at {position.trigger=}"))

        elif position.trigger == 0:  # This is the case where it does not has a trigger.
            logger.debug(f"{position.trigger=} == 0. Therefore there is no old order")
            position.trigger = high - std
            logger.debug(f"{position.trigger=} = {high=} - {std=}")
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
            logger.debug(f"{position.trigger=} > 0. Therefore old order")
            # If the old trigger is lower then the new trigger it means the price has risen. Therefore the trigger should not be moved.
            # The new trigger becomes the old trigger
            new_trigger = low + std_before
            if position.trigger < new_trigger:
                new_trigger = position.trigger
            logger.debug(f"Buy Trigger before adding {std_delta=}: {new_trigger=}")
            new_trigger = new_trigger + std_delta
            logger.debug(f"Buy Trigger after adding {std_delta=}: {new_trigger=}")

            # Check if the new calculated trigger is above current trade price. if not keep the old trigger
            if new_trigger > last_trade_price:
                # Set trigger above the current low to execute a buy as soon as the price rises
                logger.debug(f"Trigger was bigger then {last_trade_price=}. As this buy, position trigger will be set to {new_trigger=}")
                position.trigger = new_trigger
            else:
                logger.debug((f"Trigger was smaller then {last_trade_price=}. As this is a buy, position trigger will stay at {position.trigger=}"))

        elif position.trigger == 0:  # This is the case where it does not has a trigger.
            logger.debug(f"{position.trigger=} == 0. Therefore there is no old order")
            position.trigger = low + std
            logger.debug(f"{position.trigger=} = {low=} + {std=}")
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

    # Resolve the interval from string to int
    stdi = get_interval_as_int(std_interval)
    mmi = get_interval_as_int(minmax_interval)

    df_ohlc_minmax = get_ohlc_dataframe(pair=position.exchange_currency_pair, interval=mmi)
    high = get_indicator_form_ohlc(df=df_ohlc_minmax, indicator="max", history_length=minmax_history)
    low = get_indicator_form_ohlc(df=df_ohlc_minmax, indicator="min", history_length=minmax_history)
    position.current_high = high
    position.current_low = low

    # Collect two std's. The current and one period before. This way I can compare if the std has changed.
    df_ohlc_std = get_ohlc_dataframe(pair=position.exchange_currency_pair, interval=stdi)
    std = get_indicator_form_ohlc(df=df_ohlc_std, indicator="std", history_length=std_history)
    if position.current_std == 0:
        std_before = std
    else:
        std_before = position.current_std
    position.current_std = std

    last_trade_price = get_last_trade_price(position.exchange_currency_pair)
    position.current_trade_price = last_trade_price

    print(f"\n"
          f"Old Standard Deviation: {std_before} / New Standard Deviation: {std} / High Price: {high} {position.quote_currency} / Low Price: {low} {position.quote_currency} / Last Trade Price: {last_trade_price}")

    if order is not None:
        logger.debug(f"There was an order provided. Calculate stop loss trigger based on existing order. Trigger Price was {order.price} {order.quote_currency}")
        position.trigger = Decimal(order.price)

    # Update Trigger
    print(f"Current Trigger: {position.trigger} {position.quote_currency}")
    position = set_new_trigger(position, std, std_before, high, low, last_trade_price)
    print(f"New Trigger: {position.trigger} {position.quote_currency}")

    return position
