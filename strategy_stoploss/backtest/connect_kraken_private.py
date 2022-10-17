import json

import pandas as pd
import os
from decimal import Decimal
import pickle

from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader

with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")

dir_path = os.path.dirname(os.path.realpath(__file__))


def get_account_balance(key_type="backtest"):
    # Get the current account balance

    # Create the dict structure as per kraken
    json_response = {'error': [],
                     'result': {
                     }}
    filename = "current_account_balance.pickle"

    # Check if there is already a balance. If not create it from config.
    try:
        with open(f'{dir_path}/data/{filename}', 'rb') as handle:
            balance_dict = pickle.load(handle)
    except FileNotFoundError:
        logger.debug(f"{filename} not found. Create it now.")
        balance_dict = {cfg["backtest"]["start_base_currency"]: cfg["backtest"]["start_base_volume"],
                        cfg["backtest"]["start_quote_currency"]: cfg["backtest"]["start_quote_volume"]}
        with open(f'{dir_path}/data/{filename}', 'wb') as handle:
            pickle.dump(balance_dict, handle)

    json_response["result"] = balance_dict

    return json_response


def get_open_orders(key_type="backtest"):
    # Get open Orders

    # Create the dict structure as per kraken

    filename = "current_open_orders.json"

    try:
        with open(f'{dir_path}/data/{filename}', 'r') as handle:
            json_response = json.load(handle)
    except FileNotFoundError:
        # Creates a new file with initial values
        logger.debug(f"{filename} not found. Create it now.")
        initial_open_order_json_path = "strategy_stoploss/backtest/initial_content/initial_open_order.json"
        with open(initial_open_order_json_path, "r") as jsonFile:
            json_response = json.load(jsonFile)
            with open(f'{dir_path}/data/{filename}', 'w') as handle:
                json.dump(json_response, handle)

        # Sets the json response to look like an empty response.
        # This way the pickle already has the full response structure while the response of the function looks the same as for kraken
        json_response = {'error': [],
                         'result': {
                             'open':
                                 {}
                         }}

    return json_response


def trade_add_order(trade_dict, key_type):
    # Creates a new order on kraken
    json_response = {}
    return json_response, True


def trade_edit_order(trade_dict, key_type):
    # Edits a Order
    json_response = {}
    return json_response, True
