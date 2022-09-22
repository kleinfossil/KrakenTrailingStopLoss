from dataclasses import dataclass
import pandas as pd
from decimal import Decimal
import time

from stoploss.collect_data_market import (get_ohlc_dataframe,
                                          get_indicator_form_ohlc,
                                          get_last_trade_price)
from stoploss.data_classes.Position import Position

from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level)

logger = get_logger("stoploss_logger")


@dataclass
class StopLoss_Trigger:
    df_ohlc_minmax: pd.DataFrame()
    df_ohlc_std: pd.DataFrame()
    position: Position
    last_trigger_calculation: time.time = 0
    last_low: Decimal = 0
    last_high: Decimal = 0
    last_std: Decimal = 0
    last_execution_time = 0
    last_trade_price = Decimal = 0

    def __init__(self, position, std_interval, std_history, minmax_interval, minmax_history):
        self.position = position
        self.calculate_trigger(std_interval, std_history, minmax_interval, minmax_history)

    def get_position(self):
        return self.position

    def get_last_execution_time(self):
        return self.last_execution_time

    def update_ohlc_minmax(self, minmax_interval):
        self.df_ohlc_minmax = get_ohlc_dataframe(pair=self.position.exchange_currency_pair, interval=minmax_interval)

    def update_ohlc_std(self, std_interval):
        self.df_ohlc_std = get_ohlc_dataframe(pair=self.position.exchange_currency_pair, interval=std_interval)

    def update_position(self, new_position):
        self.position = new_position

    def set_execution_time(self):
        self.last_execution_time = time.time()

    def set_trigger(self, std, high, low, last_trade_price):
        self.last_std = Decimal(std)
        self.last_low = Decimal(low)
        self.last_high = Decimal(high)
        self.last_trade_price = Decimal(last_trade_price)

        # Sell Position
        if self.position.current_volume_of_base_currency > 0:
            logger.debug(f"Calculate Sell Trigger because {self.position.current_volume_of_base_currency} {self.position.base_currency} is not 0")
            # Set trigger below the current high to execute a sell as soon as the price falls
            self.position.trigger = self.last_high - self.last_std
            if self.position.trigger > self.last_trade_price:
                # Ensure that the trigger is always below the trading price
                self.position.trigger = self.last_trade_price - self.last_std

        # Buy Position
        else:
            logger.debug(f"Calculate Buy Trigger because {self.position.current_volume_of_base_currency} {self.position.base_currency} is equal 0")
            # Set trigger above the current low to execute a buy as soon as the price falls
            self.position.trigger = self.last_low + self.last_std
            if self.position.trigger < self.last_trade_price:
                # Ensure that the trigger is always above the trading price
                self.position.trigger = self.last_trade_price + self.last_std

    # Trigger will be only moved if there was movement into the expected direction
    def set_moving_trigger(self, std, high, low, last_trade_price):

        # If the low delta is negative it means that the price got lower then the last low
        low_delta = Decimal(low) - self.last_low
        # If the high delta is positive it means that the price got higher then the last high
        high_delta = Decimal(high) - self.last_high

        # If the price is lower then the last low or higher then the last high, then move the price
        if high_delta > 0 or low_delta < 0:
            logger.info(f"Move Trigger. High Delta: {high_delta} {self.position.quote_currency} , Low Delta {low_delta} {self.position.quote_currency}")
            self.set_trigger(std, high, low, last_trade_price)

        self.last_std = Decimal(std)
        self.last_low = Decimal(low)
        self.last_high = Decimal(high)
        self.last_trade_price = Decimal(last_trade_price)

    def calculate_trigger(self, std_interval, std_history, minmax_interval, minmax_history):
        self.update_ohlc_minmax(minmax_interval)
        self.update_ohlc_std(std_interval)

        std = get_indicator_form_ohlc(df=self.df_ohlc_std, indicator="std", history_length=std_history)
        high = get_indicator_form_ohlc(df=self.df_ohlc_minmax, indicator="max", history_length=minmax_history)
        low = get_indicator_form_ohlc(df=self.df_ohlc_minmax, indicator="min", history_length=minmax_history)
        last_trade_price = get_last_trade_price(self.position.exchange_currency_pair)

        print(f"\n"
              f"Standard Deviation: {std} / High Price: {high} {self.position.quote_currency} / Low Price: {low} {self.position.quote_currency} / Last Trade Price: {last_trade_price}\n"
              f"Current Trigger: {self.position.trigger} {self.position.quote_currency}")

        if self.position.trigger == 0:
            self.set_trigger(std, high, low, last_trade_price)
        else:
            self.set_moving_trigger(std, high, low, last_trade_price)

        print(f"New Trigger: {self.position.trigger} {self.position.quote_currency} \n")

        self.set_execution_time()

        return self.position