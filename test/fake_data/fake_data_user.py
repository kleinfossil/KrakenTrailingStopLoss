def fake_get_account_balance_per_currency(currencies):

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
