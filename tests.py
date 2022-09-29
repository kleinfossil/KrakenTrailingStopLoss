from stoploss.connect_kraken_private import query_order_info, get_open_orders, get_trades_history, get_trade
from stoploss.collect_data_user import get_open_orders_for_currency_pair, get_account_balance_per_currency

# just some methods to test methods directly
from report_trades import get_closed_trades_for_reporting


def test_query_order_info():
    transaction_id = "OYO4OE-TKGKH-YF3T4N"
    key = "query"
    resp = query_order_info(txid=transaction_id, key_type=key)
    print("bla")


def test_get_open_orders():
    resp = get_open_orders(key_type="query")
    print("bla")
    return resp


def test_get_closed_orders():
    #resp = get_closed_orders(key_type="query")
    resp = get_closed_trades_for_reporting()
    print(resp)
    return resp


def test_get_only_ETH_tx():
    resp = get_open_orders_for_currency_pair("XETHZEUR")
    txids = []
    for order in resp:
        txids.append(order)
    print(resp)
    price = resp[txids[0]]["descr"]["price"]
    price2 = resp[txids[0]]["descr"]["price2"]
    volume = resp[txids[0]]["vol"]
    bstype = resp[txids[0]]["descr"]["type"]

    print(f"{price=}, {price2=}, {volume=}, {bstype=}")


def test_get_account_balances():
    balances = get_account_balance_per_currency("XETHZEUR")
    print(balances)


def test_trades_and_trade():
    resp = get_trades_history("query")
    trade1 = get_trade(txid="T4VS4V-P4NVI-36INYF", key_type="query")
    trade2 = get_trade(txid="TSFQT7-DU4PP-JJBKVY", key_type="query")
    trade3 = get_trade(txid="TLVNLA-37EIJ-OF2EUN", key_type="query")


if __name__ == "__main__":
    #test_query_order_info()
    #test_get_open_orders()
    test_get_closed_orders()
    # test_get_only_ETH_tx()
    # test_get_account_balances()
    # test_trades_and_trade()
    print("done")