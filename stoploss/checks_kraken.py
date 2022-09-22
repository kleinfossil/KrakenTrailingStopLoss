from decimal import Decimal
from stoploss.collect_data_user import get_account_balance
from stoploss.connect_kraken_private import get_open_orders
import yaml
from yaml.loader import SafeLoader
from stoploss.helper_scripts.helper import get_logger
logger = get_logger("stoploss_logger")

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def check_order(trade_variable):
    if check_if_supported_asset_pair(trade_variable) \
            and check_if_order_volume_high_enough(trade_variable) \
            and check_available_funds(trade_variable):
        order_valid = True
    else:
        order_valid = False
    return order_valid


def check_if_supported_asset_pair(trade_variable):
    pair = trade_variable.pair
    supported_currencies = cfg["trading"]["supported_currencies"]
    if pair in supported_currencies:
        currency_supported = True
        logger.debug(f"{pair=} is a supported currency")
    else:
        currency_supported = False
        logger.warning(f"{pair=} is not a supported currency. Supported currencies are: {supported_currencies}")
    return currency_supported


# Checks if the order Volume is to low
def check_if_order_volume_high_enough(trade_variable):

    kraken_min_order = round(Decimal(cfg["kraken_trade"]["minimum_order"][trade_variable.pair]), 3)
    volume = Decimal(trade_variable.volume)

    if volume >= kraken_min_order:
        logger.debug(f"{volume=} >= {kraken_min_order=}. Order is higher or equal min Order")
        volume_high_enough = True
    else:
        logger.warning(f"{volume=} < {kraken_min_order=}. Order to low. Raise Order to {kraken_min_order} or higher")
        volume_high_enough = False
    return volume_high_enough


def check_available_funds(trade_variable):
    # Checks if the funds are available

    # Step1: Get currently blocked funds due to other orders
    blocked_funds = get_blocked_funds(trade_variable)

    # Step2: Collect the current account balance and add the blocked funds to decide if enough funds are available
    current_account_balance = get_account_balance(key_type="query")

    bs = trade_variable.type
    if bs == "sell":
        currency = trade_variable.pair[0:4]
        available_funds = Decimal(current_account_balance["result"][currency]) - blocked_funds["volume"]
        asked_funds = Decimal(trade_variable.volume)
    elif bs == "buy":
        currency = trade_variable.pair[4:8]
        available_funds = Decimal(current_account_balance["result"][currency]) - blocked_funds["volume"]
        asked_funds = Decimal(trade_variable.volume) * Decimal(trade_variable.price)
    else:
        raise RuntimeError(f"{bs} is neither buy nor sell. This order can not be executed")

    logger.info(f"{currency=} has {current_account_balance['result'][currency]} Funds available"
                f" and {blocked_funds['volume']} are blocked by other trades")

    if available_funds >= asked_funds:
        logger.info(f"For {currency=}: {available_funds=} >= {asked_funds=}. Funds available set to True")
        funds_available = True
    else:
        logger.warning(f"For {currency=}: {available_funds=} < {asked_funds=}. Funds available set to False")
        funds_available = False
    return funds_available


def get_blocked_funds(trade_variable):
    # gets open orders from Kraken. See: https://docs.kraken.com/rest/#operation/getOpenOrders
    # checks if order is buy or sell
    # collect all orders for buy and all orders for sell and provides blocked funds back. Important: Currently works for
    # EURO only

    json_data = get_open_orders(key_type="query")

    # Collect blocked funds by multiplying and adding current open order price with open order volume
    open_dict = json_data["result"]["open"]
    blocked_fiat = {"volume": 0.0, "type": "", "pair": ""}
    blocked_coin = {"volume": 0.0, "type": "", "pair": ""}
    for txid_key in open_dict.values():
        descr_dict = txid_key["descr"]
        if descr_dict["type"] == "buy":
            if descr_dict["pair"][-3:] == "EUR":
                blocked_fiat["volume"] = Decimal(blocked_fiat["volume"]) + (Decimal(descr_dict["price"])*Decimal(txid_key["vol"]))
                blocked_fiat["type"] = "buy"
                blocked_fiat["pair"] = descr_dict["pair"]
        elif descr_dict["type"] == "sell":
            if descr_dict["pair"][:3] in trade_variable.pair:
                blocked_coin["volume"] = Decimal(blocked_coin["volume"]) + Decimal(txid_key["vol"])
                blocked_coin["type"] = "sell"
                blocked_coin["pair"] = descr_dict["pair"]
        else:
            raise RuntimeError(f"{descr_dict['type']} is not a valid Order Type. Must be 'buy' or 'sell'.")

    if trade_variable.type == "buy":
        blocked_funds = blocked_fiat
    elif trade_variable.type == "sell":
        blocked_funds = blocked_coin
    else:
        raise RuntimeError(f"{trade_variable.type} is not a valid Order Type. Must be 'buy' or 'sell'.")

    return blocked_funds
