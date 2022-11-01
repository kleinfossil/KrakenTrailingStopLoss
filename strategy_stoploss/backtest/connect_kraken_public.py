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
from strategy_stoploss.backtest.manage_backtest_time import get_current_backtest_time_unix

with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")



def get_ohlc_json(pair, interval=1, since=0):
    # Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData

    # since is currently not supported for ohlc. Therefore, it will raise an error
    if since != 0:
        raise RuntimeError(f"Currently Backtest does not support 'since' in OHLC Data. Therefore this field must be '0 but it was {since}")

    # Get current active time
    backtest_time = get_current_backtest_time_unix()

    # get OHLC from file
    bt_starting_time = cfg["backtest"]["timeframe"]
    ohlc_path = f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv"
    ts_path = f"strategy_stoploss/backtest/static_data/{cfg['backtest']['ts_table_name']}"
    ohlc_df = get_ohlc_from_file(ohlc_path=ohlc_path, ts_path=ts_path, interval=interval)

    # reduce the OHLC to the limited values
    number_of_values = int(cfg["backtest"]["ohlc_values_per_response_on_kraken"])
    json_response = get_limited_ohlc_at_time(ohlc_df=ohlc_df, pair=pair, start=backtest_time, number_of_values=number_of_values)

    return json_response


def get_ohlc_from_file(ohlc_path, ts_path, interval):
    # Opens an existing OHLC in case it exists.
    # If not create an OHLC table based on the ts table provided and save it so that it is not needed to be created again
    try:
        ohlc_df = pd.read_csv(f"{ohlc_path}")
    except FileNotFoundError:
        ohlc_df = create_ohlc_df(interval=int(interval), path=ts_path)
        ohlc_df = clean_nan_values(ohlc_df)
        save_ohlc_data(ohlc_df=ohlc_df, interval=interval)
        ohlc_df = pd.read_csv(f"{ohlc_path}")
    return ohlc_df


def get_limited_ohlc_at_time(ohlc_df, pair, start, number_of_values=720):
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

    # Add vmap column with 0 value. As I did not collect this in the dataframe.
    limited_ohlc["Vmap"] = 0

    # Reorganize the columns
    new_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Vmap", "Trades"]
    limited_ohlc = limited_ohlc.reindex(columns=new_cols)
    # Make dataframe to list but keep the dtypes (tolist made everything to float)
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
    """ General Structure
    {"error":[],
        "result":
        {'XETHZEUR':
            {
                'a': ['1606.66000', '3', '3.000'],          Ask [<price>, <whole lot volume>, <lot volume>]
                'b': ['1606.37000', '1', '1.000'],          Bid [<price>, <whole lot volume>, <lot volume>]
                'c': ['1606.66000', '0.00061321'],          Last trade closed [<price>, <lot volume>]
                'v': ['3450.71273470', '8677.89702142'],    Volume [<today>, <last 24 hours>]
                'p': ['1605.45723', '1593.94790'],          Volume weighted average price [<today>, <last 24 hours>]
                't': [8469, 28773],                         Number of trades [<today>, <last 24 hours>]
                'l': ['1586.56000', '1565.16000'],          Low [<today>, <last 24 hours>]
                'h': ['1624.29000', '1638.33000'],          High [<today>, <last 24 hours>]
                'o': '1591.22000'                           Today's opening price
            }
        }
    """
    # The Backtest will just mock the closing price for now. All other values will be set to 0
    # First create the basic template for the response dict
    response_dict = {
        "error": [],
        "result": {
            pair:
                {'a': ['0.00', '0', '0.00'],
                 'b': ['0.00', '0', '0.00'],
                 'c': ['0.00', '0.00'],
                 'v': ['0.00', '0.00'],
                 'p': ['0.00', '0.00'],
                 't': [0.00, 0.00],
                 'l': ['0.00', '0.00'],
                 'h': ['0.00', '0.00'],
                 'o': '0.00'
                 }
            }
        }



    backtest_time = get_current_backtest_time_unix()

    # Open ts-table
    ts_path = f"strategy_stoploss/backtest/static_data/{cfg['backtest']['ts_table_name']}"
    ts_df = open_ts_table(ts_path)

    # Select the closing price equal or earlier than backtest_time
    trades_earlier_than_backtest_time = ts_df.loc[(ts_df["Unix_Date"] <= backtest_time)]
    # It is possible that the ts-table does not contain a value which is below the backtest_time.
    # In this case it will use the first value of the ts-table as price
    if len(trades_earlier_than_backtest_time) == 0:
        trades_earlier_than_backtest_time = ts_df.iloc[0]
    # It is possible that just one trade is selected. In this case iloc can not be used.
    try:
        last_trade_closed_price = trades_earlier_than_backtest_time["Price"].iloc[-1]
    except AttributeError:
        last_trade_closed_price = trades_earlier_than_backtest_time["Price"]

    response_dict["result"][pair]["c"] = [str(last_trade_closed_price), '0.00']

    # I am dumping it once into json to ensure that the structure is correct
    json_response = json.dumps(response_dict)
    # Then load it again, so that it is not a string but a dict.
    return json.loads(json_response)


def get_asset_pairs(pair):
    # Gets Kraken asset Pairs
    response_dict = {
        'error': [],
        'result': {
            'XETHZEUR': {
                'altname': 'ETHEUR',
                'wsname': 'ETH/EUR',
                'aclass_base':
                'currency',
                'base': 'XETH',
                'aclass_quote': 'currency',
                'quote': 'ZEUR',
                'lot': 'unit',
                'cost_decimals': 5,
                'pair_decimals': 2,
                'lot_decimals': 8,
                'lot_multiplier': 1,
                'leverage_buy': [2, 3, 4, 5],
                'leverage_sell': [2, 3, 4, 5],
                'fees': [[0, 0.26], [50000, 0.24], [100000, 0.22], [250000, 0.2], [500000, 0.18], [1000000, 0.16], [2500000, 0.14], [5000000, 0.12], [10000000, 0.1]],
                'fees_maker': [[0, 0.16], [50000, 0.14], [100000, 0.12], [250000, 0.1], [500000, 0.08], [1000000, 0.06], [2500000, 0.04], [5000000, 0.02], [10000000, 0.0]],
                'fee_volume_currency': 'ZUSD',
                'margin_call': 80,
                'margin_stop': 40,
                'ordermin': '0.01',
                'costmin': '0.45',
                'tick_size': '0.01'
                }
            }
        }
    # I am dumping it once into json to ensure that the structure is correct
    json_response = json.dumps(response_dict)
    # Then load it again, so that it is not a string but a dict.
    return json.loads(json_response)
