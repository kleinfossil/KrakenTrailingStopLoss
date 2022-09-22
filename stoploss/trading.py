from stoploss.data_classes.Position import Position
from decimal import Decimal
from stoploss.data_classes.kraken_data_classes import AddTrade
from stoploss.execute_kraken_add_edit_cancel import execute_order
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def add_order(position, buy_sell_type, volume, price, price2, trade_reason_message="NOT PROVIDED"):
    # Round Price and Volume to the allowed numbers of decimals before trade

    # Price is the main price, or the trigger for stop loss
    price = Decimal(round(price, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["price_decimals"])))

    # Price2 is the limit price for stop loss
    price2 = Decimal(round(price2, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["price_decimals"])))

    # Volume is the amount of base currency to be bought or sold
    volume = Decimal(round(volume, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["volume_decimals"])))

    # Create a new trade using price and volume
    print("--------> Trade------->")
    print(f"Trade Reason: {trade_reason_message}")
    print("")
    print(f"Assets before Trade:")
    print(position)
    print("")
    print(f"Order: {buy_sell_type} - {position.exchange_currency_pair} - Volume: {volume} - Trigger: {price} - Limit Price: {price2} - Order Value: {volume * price}")
    print("")

    userref = position.position_number
    order_type = cfg["kraken_trade"]["order_type"]
    trade = AddTrade(userref=userref, ordertype=order_type, type=buy_sell_type,
                     volume=str(volume), pair=position.exchange_currency_pair,
                     price=str(price), price2=str(price), timeinforce="GTC", validate="true")
    # Step 3: Check if the trade requires any pre-trade executions. If not, execute Trade
    # --> At this point the trade will be handover to Kraken
    resp_json, trade_execution_check = execute_order(trade)
    trade = post_trade_execution_activities(resp_json, trade_execution_check, trade)
    print("<----------------------")

    return trade


def post_trade_execution_activities(self, resp_json, trade_execution_check, trade):
    return trade