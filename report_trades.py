from stoploss.connect_kraken_private import get_closed_orders
from stoploss.helper_scripts.helper import get_logger, convert_unix_time_to_datetime
import pandas as pd
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def manage_book(book_name):
    all_trades_book = open_book(book_name)
    initial_trade_list = transform_order_into_book(get_latest_orders())
    last_response_txid = initial_trade_list[-1]["txid"]
    first_response_txid = initial_trade_list[0]["txid"]
    all_trades_book = append_to_book(name=book_name, book=all_trades_book, book_entries=initial_trade_list)
    while (last_response_txid != first_response_txid) or (last_response_txid):
        next_trade_list = transform_order_into_book(get_closed_orders(key_type="query", till=last_response_txid))
        all_trades_book = append_to_book(name=book_name, book=all_trades_book, book_entries=next_trade_list)
        first_response_txid = next_trade_list[0]["txid"]
        last_response_txid = next_trade_list[-1]["txid"]
        print(last_response_txid)
        print(first_response_txid)
    save_files(name=book_name, book=all_trades_book)

    return all_trades_book


def transform_order_into_book(resp_json):
    orders = resp_json["result"]["closed"]
    all_txids = []
    for order in orders:
        all_txids.append(order)
    dict_list = []
    for txid in all_txids:
        trade_details = {
            "txid": txid,
            "userref": orders[txid]["userref"],
            "status": orders[txid]["status"],
            "open_time_unix": orders[txid]["opentm"],
            "close_time_unix": orders[txid]["closetm"],
            "open_time": convert_unix_time_to_datetime(orders[txid]["opentm"]),
            "close_time": convert_unix_time_to_datetime(orders[txid]["closetm"]),
            "pair": orders[txid]["descr"]["pair"],
            "type": orders[txid]["descr"]["type"],
            "order_type": orders[txid]["descr"]["ordertype"],
            "order_trigger": orders[txid]["descr"]["price"],
            "order_limit": orders[txid]["descr"]["price2"],
            "order_volume": orders[txid]["vol"],
            "executed_volume": orders[txid]["vol_exec"],
            "executed_trigger": orders[txid]["stopprice"],
            "executed_limit": orders[txid]["limitprice"],
            "total_cost": orders[txid]["cost"],
            "total_fee": orders[txid]["fee"],
            "avg_price": orders[txid]["price"],
            "misc": orders[txid]["misc"],
            "oflags": orders[txid]["oflags"],
        }
        if "trades" in orders[txid]:
            trade_details["related_trades"] = orders[txid]["trades"]
        else:
            trade_details["related_trades"] = ""

        dict_list.append(trade_details)
    return dict_list


def open_book(name):
    # Create Book
    try:
        db_path = cfg['basic']['book-storage-location'] + name + "_book.csv"
        logger.debug(f"Opening book at {db_path}")
        df_book = pd.read_csv(db_path)
    except pd.errors.EmptyDataError:
        logger.warning(f"{name} Book csv was empty. This is normal if the program runs for the first time. "
                       f"The {name} book will be initialised now.")
        df_book = init_book(name)
    except FileNotFoundError:
        logger.warning(f"{name} Book csv did not existed. This is normal if the program runs for the first time. "
                       f"The {name} book will be initialised now.")
        df_book = init_book(name)
    else:
        logger.debug(f"{name} book loaded into memory")
    return df_book


def init_book(name):
    df = pd.DataFrame()
    df.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    return df


def append_to_book(name, book, book_entries):
    append_df = pd.DataFrame(book_entries)
    book = pd.concat([book, append_df])


    return book


def save_files(name, book):
    book.drop_duplicates(subset=["txid"], keep="first", inplace=True)
    book.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    logger.info(f"Book saved at: {cfg['basic']['book-storage-location']}{name}_book.csv")
    excel_book = pd.read_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv")
    excel_book.to_excel((f"{cfg['basic']['book-storage-location']}{name}_book.xlsx"))
    logger.info(f"Book saved at: {cfg['basic']['book-storage-location']}{name}_book.xlsx")


def get_latest_orders():
    resp_json = get_closed_orders(key_type="query")
    return resp_json


def get_closed_trades_for_reporting(book, till="OLHFIA-WPUQN-XZ4PF6"):
    resp_json = get_closed_orders(key_type="query", till=till)
    orders = resp_json["result"]["closed"]
    closed_txids = []
    all_txids = []
    for order in orders:
        all_txids.append(order)
        if orders[order]["status"] == "closed":
            closed_txids.append(order)
    dict_list = []
    for txid in all_txids:
        trade_details = {
            "txid":             txid,
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
        }
        if "trades" in orders[txid]:
            trade_details["related_trades"] = orders[txid]["trades"]
        else:
            trade_details["related_trades"] = ""

        dict_list.append(trade_details)

    book_name = "all_orders"
    append_to_book(book_name, book, dict_list)


if __name__ == "__main__":
    #active_book = init_book("all_orders4")
    #get_closed_trades_for_reporting(active_book)
    #get_latest_orders()
    manage_book("all_orders5")




