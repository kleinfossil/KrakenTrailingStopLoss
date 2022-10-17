# Script functions which extract and transform data
import traceback
import pandas as pd
from strategy_stoploss.connect_kraken_public import (
    get_ohlc_json,
    get_ticker)
from strategy_stoploss.helper_scripts.helper import (
    convert_unix_time_to_datetime,
    get_stdev,
    get_logger)

logger = get_logger("stoploss_logger")


def get_ohlc_dataframe(pair, interval):
    # Collect ohlc data and return a dataframe from a json
    ohlc_json_output = get_ohlc_json(pair=pair, interval=interval)
    ohlc_df = transform_ohlc_json_to_ohlc_dataframe(ohlc_json_output, pair)
    ohlc_df["Date"] = ohlc_df["Date"].apply(convert_unix_time_to_datetime)
    return ohlc_df


def transform_ohlc_json_to_ohlc_dataframe(json_data, api_symbol):
    # Creates a readable dataframe out of the json from kraken

    list_to_collect_data = []

    for trade in json_data["result"][api_symbol]:
        # 0: Unix epoch time
        # 1: Open - The first traded price
        # 2: High - The highest traded price
        # 3: Low - The lowest traded price
        # 4: Close - The final traded price
        # 5: VWAP - Volume-weighted average price
        # 6: Volume - The total volume traded by all trades
        # 7: Trades - The number of individual trades

        list_to_collect_data.append(trade)

    column_names = ["Date", "Open", "High", "Low", "Close", "Vwap", "Volume", "Trades"]
    kraken_dataframe = pd.DataFrame(list_to_collect_data, columns=column_names)
    kraken_dataframe[["Open", "High", "Low", "Close", "Vwap", "Volume", "Trades"]] = \
        kraken_dataframe[["Open", "High", "Low", "Close", "Vwap", "Volume", "Trades"]].apply(pd.to_numeric)

    return kraken_dataframe



def get_indicator_form_ohlc(df, indicator, history_length=24):
    # gets a value from the OHLC dataframe based on the indicator. History Length says how far the function should look back. default are the last 24 values
    try:
        match indicator:
            case "max": indicator_value = get_ohlc_max(df=df, history_length=history_length)
            case "min": indicator_value = get_ohlc_min(df=df, history_length=history_length)
            case "std": indicator_value = get_ohlc_standard_deviation(df=df, history_length=history_length)
            case _: raise ValueError(f"Could not find Indicator: {indicator}")

        return indicator_value
    except ValueError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def get_ohlc_max(df, history_length):
    # get the max of a specific timeframe
    return df["High"].tail(history_length).max()


def get_ohlc_min(df, history_length):
    # get the min of a specific timeframe
    return df["Low"].tail(history_length).min()


def get_ohlc_standard_deviation(df, history_length):
    # Returns the standard deviation
    return get_stdev(df["Close"].tail(history_length))


def get_last_trade_price(pair):
    # Returns the last ticket price
    resp = get_ticker(pair)
    value = resp["result"][pair]["c"][0]
    return value
