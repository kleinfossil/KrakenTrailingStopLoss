import os
import shutil

dir_path = os.path.dirname(os.path.realpath(__file__))
main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"
os.chdir(main_dir_path)

from strategy_stoploss.backtest.connect_kraken_public import get_ohlc_from_file
from strategy_stoploss.backtest.manage_backtest_time import set_backtest_starting_time, set_backtest_time, set_backtest_forward
from strategy_stoploss.helper_scripts.helper import get_logger, convert_datetime_to_unix_time
from strategy_stoploss.backtest.connect_kraken_private import get_open_orders, get_account_balance
import yaml
from yaml.loader import SafeLoader

from strategy_stoploss.strategy_stop_loss_helper import get_interval_as_int

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)
with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    backtest_cfg = yaml.load(yml_file, Loader=SafeLoader)
logger = get_logger("backtest_logger")



def clean_backtest_runtime_data():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"
    os.chdir(main_dir_path)
    folder = 'strategy_stoploss/backtest/runtime_data'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error('Failed to delete %s. Reason: %s' % (file_path, e))


def init_backtest(backtest):
    # Backtests allow the program to run with data from file instead using the market API.

    if backtest == 1:
        clean_backtest_runtime_data()
    backtest_starting_time = set_backtest_starting_time(backtest)

    std_interval = cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_interval"]
    std_history = cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_history"]
    minmax_interval = cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_interval"]
    minmax_history = cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_history"]

    stdi = get_interval_as_int(std_interval)
    minmaxi = get_interval_as_int(minmax_interval)

    stdi = stdi*int(std_history)*60+1
    minmaxi = minmaxi*int(minmax_history)*60+1

    if stdi >= minmaxi:
        backtest_time_offset = backtest_starting_time + stdi
    else:
        backtest_time_offset = backtest_starting_time + minmaxi

    set_backtest_time(backtest_time_offset)

    return backtest_time_offset


def post_trade_backtest(position):
    new_backtest_time = set_backtest_forward()
    bt_starting_time = backtest_cfg["backtest"]["timeframe"]
    interval = int(float(cfg["trading"]["waiting_time"])/60)
    ohlc_path = f"strategy_stoploss/backtest/static_data/{bt_starting_time}_{interval}_ohlc.csv"
    ts_path = f"strategy_stoploss/backtest/static_data/{backtest_cfg['backtest']['ts_table_name']}"
    ohlc_df = get_ohlc_from_file(ohlc_path=ohlc_path, ts_path=ts_path, interval=interval)
    ohlc_df["Date"] = ohlc_df["Date"].apply(lambda x: int(convert_datetime_to_unix_time(date_time=x, time_format="%Y-%m-%d %H:%M:%S")))
    limited_ohlc = ohlc_df.loc[ohlc_df["Date"] <= new_backtest_time]
    last_ohlc = limited_ohlc.iloc[-1]

    open_order = get_open_orders(key_type="backtest")
    """Example Order
    {'error': [], 'result': {'open': {'KAS3AM-4Y5QV-UJPT7M': {'refid': 'None', 'link_id': 'KASLUM-B6WBI-4HACIO', 'userref': 'backtest', 'status': 'open', 'opentm': '', 'starttm': '0', 'expiretm': '0', 'descr': {'pair': 'ETHEUR', 'type': 'buy', 'ordertype': 'stop-loss-limit', 'price': '1376.66', 'price2': '1377.66', 'leverage': 'none', 'order': '', 'close': ''}, 'vol': '0.70409121', 'vol_exec': '0.00000000', 'cost': '0.00000', 'fee': '0.00000', 'price': '0.00000', 'stopprice': '0.00000', 'limitprice': '0.00000', 'misc': '', 'oflags': 'fciq'}}}}"""
    orders = []
    for order in open_order["result"]["open"]:
        orders = orders.append(order)
    if len(orders) == 1:
        if (orders[0]["descr"]["type"] == "buy") & (orders[0]["descr"]["ordertype"] == "stop-loss_limit"):
            if last_ohlc["High"] >= float(orders[0]["descr"]["price2"]):
                clean_up(f"{main_dir_path}/strategy_stoploss/backtest/runtime_data/current_open_orders.json")
                account_balance = get_account_balance(key_type="backtest")
                new_base = float(orders[0]["vol"])
                new_quote = float(account_balance[cfg["backtest"]["start_quote_currency"]]) - (new_base*float(orders[0]["descr"]["price"]))
                account_balance[cfg["backtest"]["start_base_currency"]] = new_base
                account_balance[cfg["backtest"]["start_quote_currency"]] = new_quote
        elif (orders[0]["descr"]["type"] == "sell") & (orders[0]["descr"]["ordertype"] == "stop-loss_limit"):
            if last_ohlc["Low"] <= float(orders[0]["descr"]["price2"]):
                clean_up(f"{main_dir_path}/strategy_stoploss/backtest/runtime_data/current_open_orders.json")
                account_balance = get_account_balance(key_type="backtest")
                new_base = float(orders[0]["vol"])*float(orders[0]["descr"]["price"])
                new_quote = 0.00
                account_balance[cfg["backtest"]["start_base_currency"]] = new_base
                account_balance[cfg["backtest"]["start_quote_currency"]] = new_quote

    else:
        raise RuntimeError("Backtest Order is larger then 1. Currently just one order supported")

    print("bla")


def clean_up(path):
    try:
        os.remove(path)
    except FileNotFoundError as e:
        print(e)
        pass


