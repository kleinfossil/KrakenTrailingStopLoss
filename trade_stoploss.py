import traceback
import argparse
import time
from decimal import Decimal

from stoploss.connect_kraken_private import get_open_orders
from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level,
    convert_datetime_to_unix_time,
    pretty_waiting_time)
from stoploss.collect_data_user import get_account_balance_per_currency, get_open_orders_for_currency_pair
from stoploss.data_classes.Position import Position, Order
from stoploss.strategy_stop_loss import (
    initiate_stop_loss_trigger,
    update_stop_loss_trigger,
    get_buy_or_sell_type,
    get_limit_price_and_volume, update_stop_loss_trigger2)
from stoploss.strategy_stop_loss_trigger import calculate_stop_loss_trigger
from test.fake_data.fake_data_user import fake_get_account_balance_per_currency
from stoploss.trading import add_order, edit_order
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def get_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--std_history",
        type=int,
        nargs="?",
        default=15,
        help="Number of values which should be used for the standard deviation"
    )
    parser.add_argument(
        "--minmax_history",
        type=int,
        nargs="?",
        default=24,
        help="Number values which should be used to identify minimum and maximum"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        nargs="?",
        default="DEBUG",
        help="Log level. See: https://docs.python.org/3/library/logging.html#levels"
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

    opt = parser.parse_args()
    return opt


def get_currency_pair(base_currency, quote_currency):
    try:
        if (base_currency == "XETH") and (quote_currency == "ZEUR"):
            exchange_currency_pair = "XETHZEUR"
        else:
            raise RuntimeError(f"{base_currency=} and {quote_currency=} are not a supported exchange currency pair.")
        return exchange_currency_pair
    except RuntimeError as e:
        logger.error(traceback.print_stack(),e)


def create_position(base_currency, quote_currency):
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
                                )
        return new_position
    except RuntimeError as e:
        logger.error(traceback.print_stack(),e)


def init_program():
    # Resolve provided arguments
    arguments = get_arguments()
    # set log level based on arguments
    set_log_level(logger, arguments.log_level)
    return arguments


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


def trade_position(base_currency, quote_currency):
    try:
        active_position = create_position(base_currency, quote_currency)
        if cfg["trading"]["strategy"]["stop_loss"]["active"] == 1:
            # Check open orders and the differences to the current position
            orders_in_scope = get_open_orders_for_currency_pair(active_position.exchange_currency_pair)

            # Check if more then one order exists
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
                edit_order(position=updated_position, volume=trade_dict["volume"], price=trade_dict["price"], price2=updated_position.trigger,
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
                          price=trade_dict["price"], price2=updated_position.trigger,
                          trade_reason_message="Stop Loss Strategy - New Order")
            else:
                raise RuntimeError("open positions was negative. This should be not possible")
        else:
            raise RuntimeError("No valid trading strategy found")
    except RuntimeError as e:
        logger.error(traceback.print_stack(), e)


if __name__ == "__main__":
    # Start program
    trade_arguments = init_program()
    logger.info("Program ready to trade")
    base = cfg["trading"]["position"]["base_currency"]
    quote = cfg["trading"]["position"]["quote_currency"]



    # lock finish time
    time_till_finish = convert_datetime_to_unix_time(trade_arguments.trading_time)
    logger.info(f" Trader will finish at Datetime: {trade_arguments.trading_time} / Unixtime: {time_till_finish}")

    # Start trading
    while time_till_finish >= time.time():
        trade_position(base_currency=base, quote_currency=quote)
        pretty_waiting_time(cfg["trading"]["waiting_time"])
        # update trigger with stop_loss_interval
        # update_stop_loss_trigger(stop_loss_position=stop_loss_position, repeat_time=trade_arguments.stop_loss_interval, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24)
        # trade stop loss position
        # print(f" Current StopLoss Position Trigger: {stop_loss_position.position.trigger}")


