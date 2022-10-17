# This script reports trades and creates a report of all and all closed trades
import time

from stoploss.connect_kraken_private import get_closed_orders
from stoploss.helper_scripts.helper import get_logger, convert_unix_time_to_datetime
import pandas as pd
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def manage_book(book_name):
    # Initiates a reporting book

    all_trades_book = open_book(book_name)
    last_response_txid = ""
    first_response_txid = "_"
    last_transaction_not_in_trade_list = True

    # This will collect all transactions as Kraken just returns a limit number.
    # Confusing is how Kraken works with start and end date (probably because the API was written for a user interface).
    # Kraken uses the End Date to provided data starting from this data and earlier. So it is End-Date --> everything earlier End-Date
    # Start Date provides everything until the End Date. So it is like Start Date --> Data --> End Date.
    # Means a start date with 01.10.2022 and End Date 05.10.2022 would provide all data between these dates.
    # If I want to get all the data I start with today and then move the End date back to the latest entry while start date is not used.
    while (last_response_txid != first_response_txid) and last_transaction_not_in_trade_list:
        closed_orders = get_closed_orders(key_type="query", till=last_response_txid)
        if len(closed_orders["error"]) == 0:
            next_trade_list = transform_order_into_book(closed_orders)
            first_response_txid = next_trade_list[0]["txid"]
            last_response_txid = next_trade_list[-1]["txid"]
            if not all_trades_book.empty:
                if last_response_txid in all_trades_book["txid"].values:
                    last_transaction_not_in_trade_list = False
            all_trades_book = append_to_book(book=all_trades_book, book_entries=next_trade_list)
        elif closed_orders["error"][0] == "EAPI:Rate limit exceeded":
            i = 40
            logger.info(f"API Rate Limit. Waiting: {i}")
            time.sleep(i)
        else:
            raise RuntimeError(f"API Error: {closed_orders['error']}")
    save_files(name=book_name, book=all_trades_book)
    save_files(name="closed_trades", book=create_closed_orders_book(all_trades_book))

    return all_trades_book


def create_closed_orders_book(df):
    # Takes a book with all orders and drops everything which is not marked with status "closed"

    df.drop(df[df.status != "closed"].index, inplace=True)
    return df


def transform_order_into_book(resp_json):
    # Just formats the information from Kraken to a nice report

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
    # Creates a csv file to save the data
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
    # loads an existing book

    df = pd.DataFrame()
    df.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    return df


def append_to_book(book, book_entries):
    # Appends new entries to a book

    append_df = pd.DataFrame(book_entries)
    book = pd.concat([book, append_df])

    return book


def save_files(name, book):
    # Saves all details to a book

    book.drop_duplicates(subset=["txid"], keep="first", inplace=True)
    book.sort_values(by="close_time_unix", ascending=False, inplace=True)
    book.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    logger.info(f"Book saved at: {cfg['basic']['book-storage-location']}{name}_book.csv")
    excel_book = pd.read_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv")
    excel_book.to_excel((f"{cfg['basic']['book-storage-location']}{name}_book.xlsx"))
    logger.info(f"Book saved at: {cfg['basic']['book-storage-location']}{name}_book.xlsx")


def get_latest_orders():
    # Gets latest orders

    resp_json = get_closed_orders(key_type="query")
    return resp_json


def get_closed_trades_for_reporting(book, till="OLHFIA-WPUQN-XZ4PF6"):
    # Collects all trades from Kraken.

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

    append_to_book(book, dict_list)


if __name__ == "__main__":
    # This makes it executable
    manage_book("all_orders")
