import unittest
from stoploss.connect_kraken_private import query_order_info


# just some methods to test methods directly
def test_query_order_info():
    transaction_id = "O5JQZU-CQH7F-M3L3KG"
    key = "query"
    resp = query_order_info(txid=transaction_id, key_type=key)
    print(resp)


if __name__ == "__main__":
    test_query_order_info()
