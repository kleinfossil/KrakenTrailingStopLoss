# BACKTEST!
# This is the backtest version of connect kraken private.

import json

import pandas as pd
import os
from decimal import Decimal
import pickle

from strategy_stoploss.backtest.set_kraken_private import set_open_order
from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader

with open("strategy_stoploss/backtest/backtest_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("backtest_logger")

dir_path = os.path.dirname(os.path.realpath(__file__))
main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"


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

    # Make sure that a current_open_orders.json file exists by just opening it.
    # If it exists it will do nothing, if it does not exist it will create on
    get_open_orders("backtest")

    # Set the open order with new trade dict value
    path = f"{main_dir_path}/strategy_stoploss/backtest/data/current_open_orders.json"
    set_open_order(path=path, order_dict=trade_dict)

    # Call get_open_orders() again. Now with updated values
    json_response = get_open_orders("backtest")

    return json_response, True


def trade_edit_order(trade_dict, key_type):
    # Edits a Order

    # As for a backtest there is no difference between edit and edit (as the difference is just a different kraken API, but the result is the same)
    # the trade_edit_order() just calls trade_add_order()
    # This behavior only works as long as there is just one open order. As soon as there are more, the edit order would need to search for the correct order by order ID
    json_response, trade_check = trade_add_order(trade_dict, key_type)
    return json_response, trade_check
