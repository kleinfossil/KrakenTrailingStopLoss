import json
import os
import pickle
import traceback

from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader
dir_path = os.path.dirname(os.path.realpath(__file__))
main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")


def set_account_balance(path, balance_dict):
    with open(f'{path}', 'wb') as handle:
        pickle.dump(balance_dict, handle)


def set_open_order(path, order_dict):
    # Order dict structure:
    # pair, type, price, price2, vol
    set_init_order()
    with open(f'{path}', 'r') as handle:
        order = json.load(handle)

    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["type"] = order_dict["type"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["price"] = order_dict["price"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["price2"] = order_dict["price2"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["vol"] = order_dict["volume"]
    with open(f'{path}', 'w') as handle:
        json.dump(order, handle, indent=4)


def set_init_order():
    # Creates an initital order using the template provided in initial_open_order.json

    logger.debug("Set initial order")
    filename = "current_open_orders.json"
    initial_open_order_json_path = "strategy_stoploss/backtest/initial_content/initial_open_order.json"
    try:
        with open(initial_open_order_json_path, "r") as jsonFile:
            json_response = json.load(jsonFile)
            with open(f'{dir_path}/runtime_data/{filename}', 'w') as handle:
                json.dump(json_response, handle)
    except FileNotFoundError as e:
        logger.error(traceback, e)





