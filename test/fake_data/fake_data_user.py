from stoploss.helper_scripts.helper import get_logger
logger = get_logger("stoploss_logger")


def fake_get_account_balance_per_currency(currencies):
    logger.warning("Fake Account Data is used. ")
    fake_account_balance_json = {
        "result": {
            "ETH": "0,0",
            "EUR": "1285,3"
        },
        "error": [
            "EGeneral:Invalid arguments"
        ]
    }

    balances = {}
    for currency in currencies:
        balances[currency] = fake_account_balance_json["result"][currency]

    return balances
