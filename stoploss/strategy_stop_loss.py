from stoploss.collect_data_market import get_last_trade_price


def set_sell_trigger(position):
    market_price = get_last_trade_price(position.exchange_currency_pair)
    print(f"Current Market Price: {market_price}")

    return position