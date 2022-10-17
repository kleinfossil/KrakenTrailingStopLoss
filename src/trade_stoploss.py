# This script implements the Stop Loss trading.

import sys
import traceback
import argparse
import time
from decimal import Decimal
from datetime import datetime, timedelta

from stoploss.helper_scripts.google_secretmanager import get_key_and_secret_from_google
from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level,
    convert_datetime_to_unix_time,
    pretty_waiting_time, convert_unix_time_to_datetime)
from stoploss.collect_data_user import get_account_balance_per_currency, get_open_orders_for_currency_pair
from stoploss.data_classes.Position import Position, Order
from stoploss.strategy_stop_loss_helper import (
    get_buy_or_sell_type,
    get_limit_price_and_volume)
from stoploss.strategy_stop_loss_trigger import calculate_stop_loss_trigger
from test.fake_data.fake_data_user import fake_get_account_balance_per_currency
from stoploss.trading import add_order, edit_order
from stoploss.data_classes.global_data import set_google_secret, reset_google_secret
from src.send_mail import send_error_mail
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def get_arguments():
    # Parses all arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--log_level",
        type=str,
        nargs="?",
        default="DEBUG",
        help="Log level for Stream Output. See: https://docs.python.org/3/library/logging.html#levels"
    )
    parser.add_argument(
        "--trading_time",
        type=str,
        nargs="?",
        default="2023-12-31T00:00:00+0200",
        help="RFC 3339 time stamp until which the trader should trade, e.g.: 2022-09-21T10:49:53+00:00. See: https://tools.ietf.org/html/rfc3339"
    )
    parser.add_argument(
        "--stop_loss_interval",
        type=int,
        nargs="?",
        default=1000,
        help="Time in Milliseconds how often the trader should check for a stop loss trigger move"
    )
    parser.add_argument(
        "--secret_type",
        type=str,
        nargs="?",
        default="local",
        help="Select where the secrets are located. Currently supported 'local' and 'google'"
    )

    opt = parser.parse_args()
    return opt


def get_currency_pair(base_currency, quote_currency):
    # Currently this tool just supports Ether and Euro.
    # This function should be changed at the time more currencies are implemented
    try:
        if (base_currency == "XETH") and (quote_currency == "ZEUR"):
            exchange_currency_pair = "XETHZEUR"
        else:
            raise RuntimeError(f"{base_currency=} and {quote_currency=} are not a supported exchange currency pair.")
        return exchange_currency_pair
    except RuntimeError as e:
        logger.error(traceback.print_stack(), e)


def create_position(base_currency, quote_currency, current_std):
    # A Position is a dataclass which holds important information like the currency pairs and balances.
    # This function creates the position
    try:
        exchange_currency_pair = get_currency_pair(base_currency=base_currency, quote_currency=quote_currency)
        if cfg["debugging"]["use-fake-user-balance"] == 1:
            currencies = [base_currency, quote_currency]
            balances = fake_get_account_balance_per_currency(currencies)
        elif cfg["debugging"]["use-fake-user-balance"] == 0:
            balances = get_account_balance_per_currency(exchange_currency_pair)
        else:
            raise RuntimeError(f'{cfg["debugging"]["use-fake-user-balance"]} is not valid for use-fake-user-balance in trader_config.yml')

        new_position = Position(base_currency=base_currency,
                                quote_currency=quote_currency,
                                exchange_currency_pair=exchange_currency_pair,
                                current_volume_of_base_currency=Decimal(balances[base_currency].replace(',', '.')),
                                current_volume_of_quote_currency=Decimal(balances[quote_currency].replace(',', '.')),
                                current_std=current_std
                                )
        return new_position
    except RuntimeError as e:
        logger.error(traceback.print_stack(), e)


def init_program():
    # Resolve provided arguments
    arguments = get_arguments()
    # Set log level based on arguments
    set_log_level(logger, arguments.log_level)

    # This program was planned with google secrets in mind.
    # Due to the complexity to make the program portable (and therefore runnable on google cloud) this was not yet fully implemented.
    # The program currently works only with local keys provided in the key files folder.
    if arguments.secret_type == "google":
        logger.debug(f"{arguments.secret_type=} . Therefore keys are used from google.")
        sec_dic = get_key_and_secret_from_google()
        set_google_secret(sec_dic)
    elif arguments.secret_type == "local":
        logger.debug(f"{arguments.secret_type=} . Therefore keys are used from local file.")

    return arguments


def post_program():
    # Will be used in future for post processing at the point cronjobs are implemented
    reset_google_secret()


def init_trader():
    # create position
    position = create_position(base_currency=cfg["trading"]["position"]["base_currency"], quote_currency=cfg["trading"]["position"]["quote_currency"])
    return position


def select_order_in_scope(orders_in_scope, base_currency, quote_currency, pair):
    # Collect the one order and get all important values
    txids = []
    for order in orders_in_scope:
        txids.append(order)
    price2 = Decimal(orders_in_scope[txids[0]]["descr"]["price2"])
    volume_base = Decimal(orders_in_scope[txids[0]]["vol"])
    volume_quote = price2 * volume_base
    active_order = Order(
        txid=txids[0],
        base_currency=base_currency,
        quote_currency=quote_currency,
        exchange_currency_pair=pair,
        price=Decimal(orders_in_scope[txids[0]]["descr"]["price"]),
        price2=price2,
        volume_base=volume_base,
        volume_quote=volume_quote
    )

    return active_order


def trade_position(base_currency, quote_currency, current_std):
    # Main function which trades the position of a trader

    try:
        active_position = create_position(base_currency, quote_currency, current_std)
        if cfg["trading"]["strategy"]["stop_loss"]["active"] == 1:
            # Check open orders and the differences to the current position
            orders_in_scope = get_open_orders_for_currency_pair(active_position.exchange_currency_pair)

            # Check if more than one order exists
            if len(orders_in_scope) > 1:
                raise RuntimeError(f"There is more then one open order for the pair {active_position.exchange_currency_pair}. The trader is currently not able to handle more then one transaction")

            # If Order exists. Modify this Order
            elif len(orders_in_scope) == 1:
                active_order = select_order_in_scope(orders_in_scope=orders_in_scope, base_currency=base_currency, quote_currency=quote_currency, pair=active_position.exchange_currency_pair)
                updated_position = calculate_stop_loss_trigger(position=active_position, order=active_order,
                                                               std_interval=cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_interval"],
                                                               std_history=cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_history"],
                                                               minmax_interval=cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_interval"],
                                                               minmax_history=cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_history"])

                bstype = orders_in_scope[active_order.txid]["descr"]["type"]
                trade_dict = get_limit_price_and_volume(position=updated_position, buy_sell_type=bstype)
                edit_order(position=updated_position, volume=trade_dict["volume"], price2=trade_dict["price"], price=updated_position.trigger,
                           trade_reason_message="Stop Loss Strategy - Modified Order", buy_sell_type=bstype, txid=active_order.txid)

            # Step 3: If no order, create a new order
            elif len(orders_in_scope) == 0:
                buy_sell = get_buy_or_sell_type(active_position)
                updated_position = calculate_stop_loss_trigger(position=active_position,
                                                               std_interval=cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_interval"],
                                                               std_history=cfg["trading"]["strategy"]["stop_loss"]["config"]["standard_deviation_history"],
                                                               minmax_interval=cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_interval"],
                                                               minmax_history=cfg["trading"]["strategy"]["stop_loss"]["config"]["minmax_history"])
                trade_dict = get_limit_price_and_volume(position=updated_position, buy_sell_type=buy_sell)
                add_order(position=updated_position, buy_sell_type=buy_sell, volume=trade_dict["volume"],
                          price2=trade_dict["price"], price=updated_position.trigger,
                          trade_reason_message="Stop Loss Strategy - New Order")
            else:
                raise RuntimeError("open positions was negative. This should be not possible")
            return updated_position
        else:
            raise RuntimeError("No valid trading strategy found")
    except RuntimeError as e:
        logger.error(traceback.print_stack(), e)


def post_trade(position):
    # Everything what will happen after a position was traded
    position.add_to_position_book()
    handlers = logger.handlers

    # save logfile during iteration
    for handler in handlers:
        if handler.__class__.__name__ == 'FileHandler':
            handler.close()


def exception_handling(e):
    # Send failure Message
    stack = traceback.format_exc()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    message = f"trade_stoploss.py encountered an error:\n" \
              f"Error: {e}\n" \
              f"\n" \
              f"Stacktrace:\n" \
              f"\n" \
              f"{stack}"
    if cfg["debugging"]["send_error_mails"] == 1:
        send_error_mail(message=message)
    else:
        logger.info("Send Error Mails is currently deactivated")

    # Log error
    logger.error(f"{traceback.format_tb(exc_traceback)} {e}")
    handlers = logger.handlers
    for handler in handlers:
        if handler.__class__.__name__ == 'FileHandler':
            handler.close()


if __name__ == "__main__":
    try:
        # Start program
        trade_arguments = init_program()
        logger.info("Program ready to trade")
        base = cfg["trading"]["position"]["base_currency"]
        quote = cfg["trading"]["position"]["quote_currency"]

        # lock finish time
        time_till_finish = convert_datetime_to_unix_time(trade_arguments.trading_time)
        logger.info(f" Trader will finish at Datetime: {trade_arguments.trading_time} / Unixtime: {time_till_finish}")

        # std_change is a value which should be take over from trade to trade. Therefore it is defined outside the trading loop
        std_change: Decimal = Decimal(0)

        # Start trading
        print(f"### STOP LOSS TRADER IS RUNNING ###\n"
              f"Trader will run till --> {trade_arguments.trading_time}\n")

        i = 1
        while time_till_finish >= time.time():
            current_time = convert_unix_time_to_datetime(time.time())
            print(f"_________> RUN {i} at {current_time} <_________")
            print("")
            logger.debug(f"Before trading: {std_change=}")
            traded_position = trade_position(base_currency=base, quote_currency=quote, current_std=std_change)
            std_change = traded_position.current_std
            logger.debug(f"After trading: {std_change=}")

            post_trade(traded_position)
            now = datetime.now()
            next_execution = now + timedelta(seconds=cfg["trading"]["waiting_time"])
            print(f"It is now: {now} -> Wait {cfg['trading']['waiting_time']} Seconds -> Next Execution: {next_execution}")
            if cfg["basic"]["pretty_waiting_time"] == 1:
                pretty_waiting_time(cfg["trading"]["waiting_time"])
            else:
                logger.debug("Pretty Waiting Time is deactivated.")
                time.sleep(cfg["trading"]["waiting_time"])
            i += 1

        post_program()
    except RuntimeError as e:
        exception_handling(e)
        exit(0)
    except TypeError as e:
        exception_handling(e)
        exit(0)
    except AttributeError as e:
        exception_handling(e)
        exit(0)
    except Exception as e:
        exception_handling(e)
        exit(0)
