from stoploss.connect_kraken_private import get_account_balance
from stoploss.connect_kraken_public import get_asset_pairs
from stoploss.helper_scripts.helper import get_logger
logger = get_logger("stoploss_logger")


def resolve_three_character_currency_to_kraken_currency(exchange_currency_pair):
    asset_pairs_details = get_asset_pairs(exchange_currency_pair)
    return [asset_pairs_details["result"][exchange_currency_pair]["base"], asset_pairs_details["result"][exchange_currency_pair]["quote"]]


def get_account_balance_per_currency(exchange_currency_pair):
    kraken_currencies = resolve_three_character_currency_to_kraken_currency(exchange_currency_pair)

    logger.debug("Collect real account balance ")

    json_response = get_account_balance()
    balances = {}
    for currency in kraken_currencies:
        balances[currency] = json_response["result"][currency]
    return balances
