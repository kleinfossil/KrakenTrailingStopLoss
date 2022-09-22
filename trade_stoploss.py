import argparse
from decimal import Decimal

from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level,
    convert_datetime_to_unix_time,
    convert_unix_time_to_datetime)
from stoploss.collect_data_market import (
    get_ohlc_dataframe,
    get_indicator_form_ohlc
)
from stoploss.collect_data_user import fake_get_account_balance_per_currency
from stoploss.data_classes.Position import Position
from stoploss.strategy_stop_loss import (
    initiate_stop_loss_trigger,
    update_stop_loss_trigger)
import time

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


# Just to test some functions
def test_functions(std_history, minmax_history):
    print("Start auto Trader")
    hourly_ohlc = get_ohlc_dataframe(pair="XETHZEUR", interval=60)
    daily_ohlc = get_ohlc_dataframe(pair="XETHZEUR", interval=1440)

    price_24h_min = get_indicator_form_ohlc(df=hourly_ohlc, indicator="min", history_length=minmax_history)
    price_24h_max = get_indicator_form_ohlc(df=hourly_ohlc, indicator="max", history_length=minmax_history)

    stdev_days = get_indicator_form_ohlc(df=daily_ohlc, indicator="std", history_length=std_history)

    print(f"Max: {price_24h_max}")
    print(f"Min: {price_24h_min}")
    print(f"Stdev Last {std_history} Days: {stdev_days}")


def create_position(base_currency, quote_currency):
    if (base_currency == "ETH") and (quote_currency == "EUR"):
        exchange_currency_pair = "XETHZEUR"
    else:
        raise RuntimeError(f"{base_currency=} and {quote_currency=} are not a supported exchange currency pair.")

    current_volume_of_base_currency = Decimal(fake_get_account_balance_per_currency("XETH").replace(',', '.'))
    current_volume_of_quote_currency = Decimal(fake_get_account_balance_per_currency("ZEUR").replace(',', '.'))

    new_position = Position(base_currency=base_currency,
                            quote_currency=quote_currency,
                            exchange_currency_pair=exchange_currency_pair,
                            current_volume_of_base_currency=current_volume_of_base_currency,
                            current_volume_of_quote_currency=current_volume_of_quote_currency,
                            )
    return new_position


if __name__ == "__main__":

    trade_arguments = get_arguments()
    set_log_level(logger, trade_arguments.log_level)
    # test_functions(std_history=trade_arguments.std_history, minmax_history=trade_arguments.minmax_history)
    my_position = create_position(base_currency="ETH", quote_currency="EUR")
    print(my_position)
    stop_loss_position = initiate_stop_loss_trigger(position=my_position, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24)
    time_till_finish = convert_datetime_to_unix_time(trade_arguments.trading_time)

    logger.info(f" Trader will finish at Datetime: {trade_arguments.trading_time} / Unixtime: {time_till_finish}")
    while time_till_finish >= time.time():
        # trade position
        # update trigger with stop_loss_interval
        update_stop_loss_trigger(stop_loss_position=stop_loss_position, repeat_time=trade_arguments.stop_loss_interval, std_interval="d", std_history=10, minmax_interval="h", minmax_history=24)
        # trade stop loss position
        print(f" Current StopLoss Position Trigger: {stop_loss_position.position.trigger}")


