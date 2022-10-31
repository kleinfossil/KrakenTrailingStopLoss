# This script prepares the trading date so that it can be handed over to a market like kraken.
import time
from decimal import Decimal
from strategy_stoploss.helper_scripts.helper import get_logger
from strategy_stoploss.data_classes.kraken_data_classes import AddTrade, EditOrder
from strategy_stoploss.execute_kraken_add_edit_cancel import execute_order
from strategy_stoploss.helper_scripts.format_terminal import bcolors as coloring
from strategy_stoploss.connect_kraken_private import get_closed_orders
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


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
    format_trading_message(message_type="outro", position=position, resp=resp_json)

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
        earnings_dict = get_fee_adjusted_price_and_earnings(buy_sell_type, volume, price)

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
        fee_adjusted_last_price = earnings_dict["fee_adj_price"]

        fee_adjusted_last_price = Decimal(fee_adjusted_last_price).quantize(Decimal('0.01'))
        earnings = Decimal(earnings_dict["earnings"]).quantize(Decimal('0.01'))
        last_price = Decimal(earnings_dict["last_price"]).quantize(Decimal('0.01'))

        if earnings > 0:
            print(f"Last Trade: {earnings_dict['last_type']} {last_price} / fee adj.: {fee_adjusted_last_price}. Trigger: {buy_sell_type} {price} -{coloring.OKGREEN} Win: {earnings} {coloring.ENDC}")
        else:
            print(f"Last Trade: {earnings_dict['last_type']} {last_price} / fee adj.: {fee_adjusted_last_price}. Trigger: {buy_sell_type} {price} -{coloring.WARNING} Lose: {earnings} {coloring.ENDC}")

    elif message_type == "outro":
        if resp != "":
            print(f"Kraken Response received: {resp}")
        print("<---------------------------------")
    else:
        raise RuntimeError(f"{message_type=} is not valid for formatting")


def get_fee_adjusted_price_and_earnings(buy_sell_type, volume, price):
    # Creates a status message to share with the trade if the trade is good or not

    found_closed_order = False
    first_order = ""
    last_order = "_"

    while (first_order != last_order) and not found_closed_order:
        logger.debug("Checking last Transactions on Kraken to find the last closed order. Always checking 720 at a time. ")
        orders = get_closed_orders(key_type="query", till=first_order)
        if len(orders["error"]) == 0:
            order_list = list(orders["result"]["closed"].keys())
            first_order = order_list[0]
            last_order = order_list[-1]
            for order in orders["result"]["closed"].items():
                if order[1]["status"] == "closed":
                    found_closed_order = True
                    last_trade = {
                        "volume": Decimal(order[1]["vol"]),
                        "price": Decimal(order[1]["price"]),
                        "fee": Decimal(order[1]["fee"]),
                        "cost": Decimal(order[1]["cost"]),
                        "close_time": Decimal(order[1]["closetm"]),
                        "type": order[1]["descr"]["type"],
                        "pair": order[1]["descr"]["pair"]
                    }
                    fee = Decimal(cfg["kraken_trade"]["fees"]["maker"])
                    if buy_sell_type == "buy":
                        fee_adjusted_price = last_trade["price"] - (price*volume*fee+last_trade["fee"])
                        earnings = (((last_trade["price"]*last_trade["volume"]) - (price*volume)) - ((last_trade["fee"])+(price*volume*fee))) + ((volume-last_trade["volume"])*price)
                    elif buy_sell_type == "sell":
                        fee_adjusted_price = last_trade["price"] + (price * volume * fee + last_trade["fee"])
                        earnings = (price * volume - last_trade["price"] * last_trade["volume"]) - (last_trade["fee"] + price * volume * fee)
                    else:
                        raise RuntimeError(f"Could not create Trading Status message as the closed order contained an invalid type. Type was: {last_trade['type']}")
                    earnings_dict = {
                        "last_price": last_trade["price"],
                        "fee_adj_price": fee_adjusted_price,
                        "earnings": earnings,
                        "last_type": last_trade["type"]
                    }

                    return earnings_dict
        elif orders["error"][0] == "EAPI:Rate limit exceeded":
            i = 40
            logger.info(f"API Rate Limit. Waiting: {i}")
            time.sleep(i)
        else:
            raise RuntimeError(f"API Error: {orders['error']}")






