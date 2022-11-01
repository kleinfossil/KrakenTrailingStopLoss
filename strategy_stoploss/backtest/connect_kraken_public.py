import json
import pickle
import traceback
import time

import pandas as pd
import math
import yaml
from yaml.loader import SafeLoader

from strategy_stoploss.helper_scripts.helper import convert_datetime_to_unix_time
from strategy_stoploss.helper_scripts.helper import get_logger

with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")


def get_ohlc_json(pair, interval=1, since=0):
    # Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData

    # since is currently not supported for ohlc. Therefore, it will raise an error
    if since != 0:
        raise RuntimeError(f"Currently Backtest does not support 'since' in OHLC Data. Therefore this field must be '0 but it was {since}")

    # Get current active time
    try:
        with open('strategy_stoploss/backtest/runtime_data/backtest_current_time.pickle', 'rb') as f:
            backtest_time = pickle.load(f)
    except FileNotFoundError as e:
        logger.error(traceback, e)
        exit(1)

    # Check if I have an OHLC table for this interval
    bt_starting_time = cfg["backtest"]["timeframe"]
    ohlc_path = f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv"
    ts_path = f"strategy_stoploss/backtest/static_data/{cfg['backtest']['ts_table_name']}"
    try:
        ohlc_df = pd.read_csv(f"{ohlc_path}")
    except FileNotFoundError:
        # If not create an OHLC table based on the ts table provided and save it so that it is not needed to be created again
        ohlc_df = create_ohlc_df(interval=int(interval), path=ts_path)
        ohlc_df = clean_nan_values(ohlc_df)
        save_ohlc_data(ohlc_df=ohlc_df, interval=interval)
        ohlc_df = pd.read_csv(f"{ohlc_path}")

    number_of_values = int(cfg["backtest"]["ohlc_values_per_response_on_kraken"])
    json_response = get_ohlc_as_json(ohlc_df=ohlc_df, pair=pair, start=backtest_time, number_of_values=number_of_values)

    return json_response


def get_ohlc_as_json(ohlc_df, pair, start, number_of_values=720):
    # Create the kraken response dict
    """General Structure of the Kraken OHLC:
    {
    "error": [],
    "result": {
        "XETHZEUR": [
            [
                1667167800, int <time>
                "1592.27", string <open>
                "1592.30", string <high>
                "1591.51", string <low>
                "1591.51", string <close>
                "1592.07", string <vwap>
                "1.47526219", string <volume>
                8 int <count>
            ],
            [
                1667167860,
                "1592.06",
                "1592.06",
                "1590.55",
                "1590.55",
                "1591.83",
                "0.24570000",
                4
            ],
        "last": 1667167860
        }
    }

    General Structure of OHLC csv:
    Open,High,Low,Close,Volume,Trades,Date
    """
    # change the date to unix date
    ohlc_df["Date"] = ohlc_df["Date"].apply(lambda x: int(convert_datetime_to_unix_time(date_time=x, time_format="%Y-%m-%d %H:%M:%S")))
    ohlc_df["Date"] = ohlc_df["Date"].astype("int32")

    # select just the values needed
    start = int(start)
    number_of_values = int(number_of_values)
    limited_ohlc = ohlc_df.loc[ohlc_df["Date"] >= start]
    limited_ohlc = limited_ohlc.iloc[0:number_of_values]

    # First create the basic template for the response dict
    response_dict = {
        "error": [],
        "result": {
            pair: [[]],
            "last": ""
        }
    }

    # Add vmap column with 0 value. As I did not collected this in the dataframe.
    limited_ohlc["Vmap"] = 0

    # reorganize the columns
    new_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Vmap", "Trades"]
    limited_ohlc = limited_ohlc.reindex(columns=new_cols)
    # make dataframe to list but keep the dtypes (tolist made everything to float)
    value_list = list(map(list, limited_ohlc.itertuples(index=False)))
    response_dict["result"][pair] = value_list
    response_dict["result"]["last"] = str(limited_ohlc["Date"].iloc[-1])

    # I am dumping it once into json to ensure that the structure is correct
    json_response = json.dumps(response_dict)
    # Then load it again, so that it is not a string but a dict.
    return json.loads(json_response)


def clean_nan_values(ohlc_df):
    # Sometimes in a timeframe of the OHLC no trade happened. In this case numpy will just write NaN values. Instead, the NaN values should be filled with the last close value
    start = time.time()
    logger.info(f"Cleaning ohlc values and replacing NaN. This can take some time. Process started at: {start}")
    ohlc_df[["Open", "High", "Low", "Close"]] = ohlc_df.apply(lambda x: replace_with_last_close(ohlc_df, x["Open"], x["High"], x["Low"], x["Close"], x["Date"], column="Open"), axis=1)
    ohlc_df = ohlc_df.dropna(how='any')
    end = time.time()
    logger.info(f"Process finished at: {end}. It took: {end - start} Seconds")
    return ohlc_df


def replace_with_last_close(ohlc_df, my_open, high, low, close, date, column):
    # Checks if there is a NaN value in the column. If yes it will replace this value with a former close value
    # This function will go through every row. So selecting an item will always respond with the value of the current row

    # Select the value in this specific column and row
    value = ohlc_df.loc[ohlc_df["Date"] == date][column].item()

    # Check if this is a NaN value
    if math.isnan(value):

        # Find the date related to this NaN value. If the index is e.g. Data instead just index.
        index_nan = int(ohlc_df.loc[ohlc_df["Date"] == date].index[0])

        # Find the index of this value
        idx = ohlc_df.index.get_loc(index_nan)
        try:
            # select the row below this index
            below_index = idx - 1

            # Check if the index is below 0. In this case it will just return this current NaN value. This value will be dropped later
            if below_index >= 0:

                # It is possible that the below value is also an NaN. In this case it should go even further to look for a non-NaN value.
                while below_index >= 0:

                    # Select the value to check if it is NaN
                    below_value = ohlc_df.iloc[below_index][column]
                    if math.isnan(below_value):
                        # If it is NaN then just set the index one below
                        below_index = below_index - 1
                    else:
                        # If it is not NaN then select the close value as this will be added into every column (independent if is high, low or open).
                        close_value = ohlc_df.iloc[below_index]["Close"]
                        return_value = pd.Series([close_value, close_value, close_value, close_value])
                        return return_value
            else:
                # If reached the first value return the NaN which will be dropped later.
                return pd.Series([my_open, high, low, close])

        except RuntimeError as e:
            logger.error(traceback, e)
            exit(1)
    # Returns the value if it is not NaN. In this case nothing changes.
    else:
        return pd.Series([my_open, high, low, close])


def save_ohlc_data(ohlc_df, interval):
    bt_starting_time = cfg["backtest"]["timeframe"]
    table = pd.DataFrame()
    try:
        table = pd.read_csv(f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv")
    except pd.errors.EmptyDataError:
        logger.warning(f"{bt_starting_time}_{interval}_ohlc.csv was empty. This is normal if there csv did not existed before")
    except FileNotFoundError:
        logger.warning(f"{bt_starting_time}_{interval}_ohlc.csv does not exists. This is normal if there csv did not existed before")
    else:
        logger.info(f"{bt_starting_time}_{interval}_ohlc.csv opened for saving")

    if table.empty:
        table = ohlc_df
        table.to_csv(f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv", index=False)
    else:
        combined = pd.concat([ohlc_df, table]).drop_duplicates().reset_index(drop=True)
        combined["Date"] = pd.to_datetime(combined["Date"])
        combined = combined.drop_duplicates(subset="Date", keep="first")
        combined = combined.sort_values(by=["Date"])
        combined = combined.reset_index(drop=True)
        combined.to_csv(f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv", index=False)
        logger.info(f"Saving Complete. {bt_starting_time}_{interval}_ohlc.csv contains now {len(combined)} Values")


def create_ohlc_df(interval, path):
    ts_df = open_ts_table(path)

    ts_df["Date"] = pd.to_datetime(ts_df["Date"])
    ts_df.index = ts_df["Date"]
    ts_df["Price"] = pd.to_numeric(ts_df["Price"])
    ts_df["Volume"] = pd.to_numeric(ts_df["Volume"])
    resampled_ohlc = ts_df["Price"].resample(str(interval) + "Min").ohlc()
    resampled_volume = ts_df["Volume"].resample(str(interval) + "Min").sum()
    resampled_volume.columns = ["Volume"]
    resampled_trades = ts_df["Volume"].resample(str(interval) + "Min").count()
    resampled_trades.columns = ["Trades"]
    df = pd.concat([resampled_ohlc, resampled_volume, resampled_trades], axis=1)
    df.columns = ["Open", "High", "Low", "Close", "Volume", "Trades"]
    df["Date"] = df.index
    df = df.reset_index(drop=True)

    return df


def open_ts_table(path):
    table = pd.DataFrame()
    try:
        table = pd.read_csv(f"{path}")
    except pd.errors.EmptyDataError:
        logger.warning(f"TS Table was empty. This is normal if there csv did not existed before")
    except FileNotFoundError:
        logger.warning(f"TS Table File does not exists. This is normal if there csv did not existed before")
    else:
        logger.info(f"TS-Table at {path} opened")
    return table


def get_ticker(pair):
    # Gets the latest ticket
    json_response = {}
    return json_response


def get_asset_pairs(pair):
    # Gets Kraken asset Pairs
    json_response = {}
    return json_response
