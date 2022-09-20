def fake_get_account_balance_per_currency(currency):
    fake_account_balance_json = {
        "result": {
            "XETH": "0,99987",
            "ZEUR": "27,87"
        },
        "error": [
            "EGeneral:Invalid arguments"
        ]
    }
    return fake_account_balance_json["result"][currency]
