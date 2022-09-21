import argparse
from decimal import Decimal

from stoploss.helper_scripts.helper import (
    get_logger,
    set_log_level)
from stoploss.collect_data_market import (
    get_ohlc_dataframe,
    get_indicator_form_ohlc,
    get_last_trade_price
)
from stoploss.collect_data_user import fake_get_account_balance_per_currency
from stoploss.Position import Position
from stoploss.strategy_stop_loss import set_sell_trigger

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


def calculate_trigger(position):
    if position.current_volume_of_quote_currency > 0:
        position = set_sell_trigger(position)
    return position


if __name__ == "__main__":
    trade_arguments = get_arguments()
    set_log_level(logger, trade_arguments.log_level)
    test_functions(std_history=trade_arguments.std_history, minmax_history=trade_arguments.minmax_history)
    my_position = create_position(base_currency="ETH", quote_currency="EUR")
    print(my_position)
    calculate_trigger(position=my_position)
