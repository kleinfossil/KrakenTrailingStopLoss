# This script manages the creation of CSV and excel reports (called books). Which allows to keep track what the program does
import traceback

from stoploss.helper_scripts.helper import get_logger

import pandas as pd
import yaml
from yaml.loader import SafeLoader
logger = get_logger("stoploss_logger")

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def append_to_book(name, book, book_entries):
    # Adds a new value to a book
    if name == "all_orders":
        append_df = pd.DataFrame(book_entries)
        book = pd.concat([book, append_df])
    else:
        if name == "positions":
            append_dict = book_entries
        else:
            raise RuntimeError(f"Could not append to book because {name} "
                               f"is not a valid book type. Use 'decision', 'order' or 'trade'")
        append_df = pd.DataFrame(append_dict, index=[0])
        book = pd.concat([book, append_df])

    book.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
    excel_book = pd.read_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv")
    excel_book.to_excel((f"{cfg['basic']['book-storage-location']}{name}_book.xlsx"))
    logger.info(f"Book saved at: {cfg['basic']['book-storage-location']}{name}_book.csv/xlsx")
    return book


def init_book(name):
    # Initiates books
    try:
        match name:
            case "positions":
                df = pd.DataFrame()
                df.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
            case "closed_trades":
                df = pd.DataFrame()
                df.to_csv(f"{cfg['basic']['book-storage-location']}{name}_book.csv", index=False)
            case _:
                raise ValueError(f"{name} is not a valid book. Books can be 'decision'")
        return df
    except ValueError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def open_book(name):
    # Opens books
    try:
        try:
            from pathlib import Path
            Path(cfg['basic']['book-storage-location']).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"{traceback.print_stack()} {e} \n Could not create path for books. Check configuration")
            exit(1)
        db_path = cfg['basic']['book-storage-location'] + name + "_book.csv"
        logger.debug(f"Opening book at {db_path}")
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
        logger.debug(f"{name} book loaded into memory")
    return book
