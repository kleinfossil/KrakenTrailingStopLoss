import json
import pickle

from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")


def set_account_balance(path, balance_dict):
    with open(f'{path}', 'wb') as handle:
        pickle.dump(balance_dict, handle)


def set_open_order(path, order_dict):
    # Order dict structure:
    # pair, type, price, price2, vol

    with open(f'{path}', 'r') as handle:
        order = json.load(handle)
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["type"] = order_dict["type"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["price"] = order_dict["price"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["descr"]["price2"] = order_dict["price2"]
    order["result"]["open"]["KAS3AM-4Y5QV-UJPT7M"]["vol"] = order_dict["volume"]
    with open(f'{path}', 'w') as handle:
        json.dump(order, handle, indent=4)

