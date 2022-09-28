from stoploss.connect_kraken_private import get_closed_orders
from stoploss.helper_scripts.helper import get_logger, convert_unix_time_to_datetime

from stoploss.report.manage_books import open_book, append_to_book

logger = get_logger("stoploss_logger")


def create_book():
    book_name = "closed_trades"
    trades_book = open_book(book_name)
    return trades_book


def get_closed_trades_for_reporting(book, start_time="1658095200"):
    resp_json = get_closed_orders(key_type="query")
    orders = resp_json["result"]["closed"]
    txids = []
    for order in orders:
        if orders[order]["status"] == "closed":
            txids.append(order)
    dict_list = []
    for txid in txids:
        trade_details = {
            "userref":          orders[txid]["userref"],
            "status":           orders[txid]["status"],
            "open_time_unix":   orders[txid]["opentm"],
            "close_time_unix":  orders[txid]["closetm"],
            "open_time":        convert_unix_time_to_datetime(orders[txid]["opentm"]),
            "close_time":       convert_unix_time_to_datetime(orders[txid]["closetm"]),
            "pair":             orders[txid]["descr"]["pair"],
            "type":             orders[txid]["descr"]["type"],
            "order_type":       orders[txid]["descr"]["ordertype"],
            "order_trigger":    orders[txid]["descr"]["price"],
            "order_limit":      orders[txid]["descr"]["price2"],
            "order_volume":     orders[txid]["vol"],
            "executed_volume":  orders[txid]["vol_exec"],
            "executed_trigger": orders[txid]["stopprice"],
            "executed_limit":   orders[txid]["limitprice"],
            "total_cost":       orders[txid]["cost"],
            "total_fee":        orders[txid]["fee"],
            "avg_price":        orders[txid]["price"],
            "misc":             orders[txid]["misc"],
            "oflags":           orders[txid]["oflags"],
            "related_trades":   orders[txid]["trades"],
        }

        dict_list.append(trade_details)

    book_name = "closed_trades"
    append_to_book(book_name, book, dict_list)


if __name__ == "__main__":
    active_book = create_book()
    get_closed_trades_for_reporting(active_book)




