import traceback

import os
from datetime import datetime
from uuid import uuid4
from stoploss.helper_scripts.helper import get_logger

import pandas as pd
import yaml
from yaml.loader import SafeLoader

logger = get_logger("stoploss_logger")

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def add_trade(trade_dict):
    book_name = "trade"
    trade_book = open_book(book_name)
    append_to_book(book_name, trade_book, trade_dict)


def append_to_book(name, book, book_entries):
    if name == "order":
        append_dict = {"Uuid": uuid4().hex,
              "Txid": book_entries["Txid"],
              "Order_datetime": book_entries["Order_datetime"],
              "Type": book_entries["Type"],
              "Pair": book_entries["Pair"],
              "Price": book_entries["Price"],
              "Volume": book_entries["Volume"],
              "Expiry_datetime": book_entries["Expiry_datetime"],
              "Decision_trigger": book_entries["Decision_trigger"],
              "Kraken_description": book_entries["Kraken_description"]
              }
    elif name == "trade":
        append_dict = book_entries
    elif name == "positions":
        append_dict = book_entries
    else:
        raise RuntimeError(f"Could not append to book because {name} "
                           f"is not a valid book type. Use 'decision', 'order' or 'trade'")
    append_df = pd.DataFrame(append_dict, index=[0])
    book = pd.concat([book, append_df])

    book.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    book.to_excel((f"{cfg['basic']['book-storage-location']}{name}_book.xlsx"))
    return book


def init_book(name):
    try:
        if name == "positions":
            df = pd.DataFrame()
            df.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
        else:
            raise ValueError(f"{name} is not a valid book. Books can be 'decision'")
        return df
    except ValueError as e:
        logger.error(f"{traceback.print_stack()} {e}")




def open_book(name):
    # Create Book
    try:
        print(cfg['basic']['book-storage-location'])
        db_path = cfg['basic']['book-storage-location'] + name + "_book.csv"
        book = pd.read_csv(db_path)
    except pd.errors.EmptyDataError:
        logger.warning(f"{name} Book csv was empty. This is normal if the program runs for the first time. "
                       f"The {name} book will be initialised now.")
        book = init_book(name)
    except FileNotFoundError:
        logger.warning(f"{name} Book csv did not existed. This is normal if the program runs for the first time. "
                       f"The {name} book will be initialised now.")
        book = init_book(name)
    else:
        logger.info(f"{name} Book loaded.")
    return book
