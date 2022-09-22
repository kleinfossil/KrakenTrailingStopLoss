from uuid import uuid4

from stoploss.collect_data_market import get_last_trade_price
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


def fake_trade_response_data(trading_variable):
    txid = uuid4().hex
    return {
            "error": [ ],
            "result": {
                "descr": {
                    "order": f"{trading_variable.type} {trading_variable.volume} {trading_variable.pair} @ "
                             f"{trading_variable.ordertype} {trading_variable.price} with {trading_variable.leverage}",
                    "close": "close position @"
                },
                "txid": [
                    f"{txid}"
                    ]
            }
        }


def fake_response_query_data(txid):
    resp_list = get_last_trade_price("XETHZEUR")
    price = resp_list[0]
    return {
                          "error": [],
                          "result": {
                            f"{txid}": {
                              "refid": "null",
                              "userref": "0",
                              "status": "closed",
                              "reason": "null",
                              "opentm": "1616665496.7808",
                              "closetm": "1616665499.1922",
                              "starttm": "0",
                              "expiretm": "0",
                              "descr": {
                                "pair": "XETHZEUR",
                                "type": "buy",
                                "ordertype": "limit",
                                "price": f"{price}",
                                "price2": "0",
                                "leverage": "none",
                                "order": "buy 1.25000000 XBTUSD @ limit 37500.0",
                                "close": ""
                              },
                              "vol": "1.25000000",
                              "vol_exec": "1.25000000",
                              "cost": "37526.2",
                              "fee": "37.5",
                              "price": f"{price}",
                              "stopprice": "0.00000",
                              "limitprice": "0.00000",
                              "misc": "",
                              "oflags": "fciq",
                              "trigger": "index",
                              "trades": [
                                "TZX2WP-XSEOP-FP7WYR"
                              ]
                            }
                          }
                        }