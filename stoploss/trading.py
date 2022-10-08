# This script prepares the trading date so that it can be handed over to a market like kraken.

from decimal import Decimal
from stoploss.data_classes.kraken_data_classes import AddTrade, EditOrder
from stoploss.execute_kraken_add_edit_cancel import execute_order
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)


def prepare_order_data(position, volume, price, price2):
    # Round Price and Volume to the allowed numbers of decimals before trade

    prepared_data = {}

    # Price is the main price, or the trigger for stop loss
    prepared_data["price"] = Decimal(round(price, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["price_decimals"])))

    # Price2 is the limit price for stop loss
    prepared_data["price2"] = Decimal(round(price2, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["price_decimals"])))

    # Volume is the amount of base currency to be bought or sold
    prepared_data["volume"] = Decimal(round(volume, int(cfg["kraken_trade"]["allowed_decimals"][position.exchange_currency_pair]["volume_decimals"])))

    prepared_data["userref"] = position.position_number
    prepared_data["order_type"] = cfg["kraken_trade"]["order_type"]

    if cfg["debugging"]["kraken"]["kraken_validation"] == 0:
        prepared_data["validate"] = "true"
    elif cfg["debugging"]["kraken"]["kraken_validation"] == 1:
        prepared_data["validate"] = "false"
    else:
        raise RuntimeError(f'{cfg["debugging"]["kraken"]["kraken_validation"]} is not a valid value to the kraken validation trigger')

    return prepared_data


def add_order(position, buy_sell_type, volume, price, price2, trade_reason_message="NOT PROVIDED"):
    data_for_trading = prepare_order_data(position=position, volume=volume, price=price, price2=price2)

    # Create a new trade using price and volume
    format_trading_message(message_type="intro", position=position, trade_reason_message=trade_reason_message, buy_sell_type=buy_sell_type,
                           volume=data_for_trading["volume"], price=data_for_trading["price"], price2=data_for_trading["price2"])

    trade = AddTrade(userref=data_for_trading["userref"], ordertype=data_for_trading["order_type"], type=buy_sell_type,
                     volume=str(data_for_trading["volume"]), pair=position.exchange_currency_pair,
                     price=str(data_for_trading["price"]), price2=str(data_for_trading["price2"]), timeinforce="GTC", validate=data_for_trading["validate"])

    # Step 3: Check if the trade requires any pre-trade executions. If not, execute Trade
    # --> At this point the trade will be handover to Kraken
    resp_json, trade_execution_check = execute_order(trade)
    format_trading_message(message_type="outro", position=position)

    return trade


def edit_order(position, txid, buy_sell_type, volume, price, price2, trade_reason_message="NOT PROVIDED"):
    data_for_trading = prepare_order_data(position=position, volume=volume, price=price, price2=price2)
    format_trading_message(message_type="intro", position=position, trade_reason_message=trade_reason_message, buy_sell_type=buy_sell_type,
                           volume=data_for_trading["volume"], price=data_for_trading["price"], price2=data_for_trading["price2"])

    modified_order = EditOrder(userref=data_for_trading["userref"], txid=txid,
                               volume=str(data_for_trading["volume"]), pair=position.exchange_currency_pair,
                               price=str(data_for_trading["price"]), price2=str(data_for_trading["price2"]), validate=data_for_trading["validate"], type=buy_sell_type)

    # Step 3: Check if the trade requires any pre-trade executions. If not, execute Trade
    # --> At this point the trade will be handover to Kraken
    resp_json, trade_execution_check = execute_order(modified_order)
    format_trading_message(message_type="outro", position=position, resp=resp_json)


def format_trading_message(message_type, position, trade_message="Trade", trade_reason_message="", buy_sell_type="", volume: Decimal = 0, price: Decimal = 0.0, price2: Decimal = 0.0, resp=None):
    # Output show on the screen during trading

    if message_type == "intro":
        print(f"---------------> {trade_message} ------------->")
        print(f"Trade Reason: {trade_reason_message}")
        print("")
        position.print_position()
        print("New Order")
        print(f"    Order: {buy_sell_type} - {position.exchange_currency_pair}\n"
              f"    Volume: {volume}\n"
              f"    Trigger: {price} - Limit Price: {price2}\n"
              f"    Order Value: {volume * price}")
        print("")
    elif message_type == "outro":
        if resp != "":
            print(f"Kraken Response received: {resp}")
        print("<---------------------------------")
    else:
        raise RuntimeError(f"{message_type=} is not valid for formatting")
