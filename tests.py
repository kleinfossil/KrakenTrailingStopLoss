import unittest
from stoploss.connect_kraken_private import query_order_info, get_open_orders
from stoploss.collect_data_user import get_open_orders_for_currency_pair
import json


# just some methods to test methods directly
def test_query_order_info():
    transaction_id = "O5JQZU-CQH7F-M3L3KG"
    key = "query"
    resp = query_order_info(txid=transaction_id, key_type=key)
    print(resp)


def test_get_open_orders():
    resp = get_open_orders(key_type="query")
    print(resp)
    return resp


def test_get_only_ETH_tx():
    resp = get_open_orders_for_currency_pair("XETHZEUR")

    print(resp)







if __name__ == "__main__":
    # test_query_order_info()
    # test_get_open_orders()
    test_get_only_ETH_tx()