# Manages user related date on Kraken

from strategy_stoploss.connect_kraken_private import get_account_balance, get_open_orders
from strategy_stoploss.connect_kraken_public import get_asset_pairs
from strategy_stoploss.helper_scripts.helper import get_logger
logger = get_logger("stoploss_logger")


def resolve_three_character_currency_to_kraken_currency(exchange_currency_pair):
    # Finds the correct kraken currency pair
    asset_pairs_details = get_asset_pairs(exchange_currency_pair)
    return [asset_pairs_details["result"][exchange_currency_pair]["base"], asset_pairs_details["result"][exchange_currency_pair]["quote"]]


def get_account_balance_per_currency(exchange_currency_pair):
    # returns the account balance per currency pair
    kraken_currencies = resolve_three_character_currency_to_kraken_currency(exchange_currency_pair)

    logger.debug("Collect real account balance ")

    json_response = get_account_balance(key_type="query")
    balances = {}
    for currency in kraken_currencies:
        balances[currency] = json_response["result"][currency]
    return balances


def get_open_orders_for_currency_pair(exchange_currency_pair):
    # Returns currently open Orders

    # Kraken changes the currency pairs when I get open orders.
    # Therefore, there is a hardcoded mapping implemented here.
    # If more than one currency pair should be supported it need to be changed here.
    match exchange_currency_pair:
        case "ZETHXEUR": exchange_currency_pair = "ETHEUR"

    resp = get_open_orders(key_type="query")
    transactions = resp["result"]["open"]
    transactions_in_scope = {}
    for transaction in transactions:
        if resp["result"]["open"][transaction]["descr"]["pair"] == "ETHEUR":
            transactions_in_scope[transaction] = resp["result"]["open"][transaction]

    return transactions_in_scope
