import argparse

from stoploss.helper_scripts.helper import get_logger
from stoploss.collect_data_market import get_ohlc_dataframe
from stoploss.collect_data_market import get_indicator_form_ohlc

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


if __name__ == "__main__":
    trade_arguments = get_arguments()
    # test_functions(std_history=trade_arguments.std_history, minmax_history=trade_arguments.minmax_history)





