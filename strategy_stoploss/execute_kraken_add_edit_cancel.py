# Manages the Orders of the Traders. This script can be seen as the Orchestrator for every Kraken Order

from strategy_stoploss.helper_scripts.helper import get_logger
from strategy_stoploss.checks_trade import check_order
from test.fake_data.fake_data_user import fake_trade_response_data
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")

if cfg["basic"]["backtest_active"] == 0:
    from strategy_stoploss.connect_kraken_private import trade_add_order, trade_edit_order
elif cfg["basic"]["backtest_active"] == 1:
    from strategy_stoploss.backtest.connect_kraken_private import trade_add_order, trade_edit_order
else:
    raise RuntimeError(f"Backtest configuration contains wrong value. Must be '1' or '0'. Value was {cfg['basic']['backtest_active']}")


def execute_order(trade_variable):
    # Place a new Order
    # See: https://docs.kraken.com/rest/

    make_trade = int(cfg["debugging"]["kraken"]["make_trade"])
    use_real_data = int(cfg["debugging"]["kraken"]["use_real_trading_data"])
    resp = {}

    # The following checks if a trade should be made. All the decisions are mainly just there as during the create the development process was not trusted.
    # Going forward this method can be reduced and decisions can be taken away.
    if make_trade == 1:
        if use_real_data == 1:
            if check_order(trade_variable):
                if ask_for_order_execution(trade_variable, make_trade, use_real_data):
                    data = trade_variable.as_dict()
                    match trade_variable.trade_type:
                        case "AddTrade":
                            resp, trade_execution_check = trade_add_order(trade_dict=data, key_type="trade")
                        case "EditOrder":
                            resp, trade_execution_check = trade_edit_order(trade_dict=data, key_type="trade")
                        case _: raise RuntimeError(f"{trade_variable.trade_type} is not a valid trading type")
                else:
                    trade_execution_check = False
                    print(f"Trade was not approved by user!")
                    logger.warning(f"User did not gave approval for trade. {trade_variable.uuid} - Trade was not executed")
            else:
                logger.exception("Not enough Funds available. Trade not executed")
                trade_execution_check = False
                resp = ""

        # This part exists for testing purposes and can be refactored in future.
        # It just exists as it was not always clear which data would arrive in the execute_order function.
        # Therefore this allowed to ensure specific data to be used for the trade.
        elif use_real_data == 0:
            logger.warning("Make a Example Trade! Change main_config 'UseRealData' to 1 for real data")
            logger.warning("Overwriting trade_variables with example data")
            trade_variable.set_example_values()
            if check_order(trade_variable):
                if ask_for_order_execution(trade_variable, make_trade, use_real_data):
                    data = trade_variable.as_dict()
                    match trade_variable.trade_type:
                        case "AddTrade":
                            resp, trade_execution_check = trade_add_order(trade_dict=data, key_type="trade")
                        case "EditTrade":
                            resp, trade_execution_check = trade_edit_order(trade_dict=data, key_type="trade")
                        case _:
                            raise RuntimeError(f"{trade_variable.trade_type} is not a valid trading type")
                else:
                    trade_execution_check = False
                    print(f"Trade was not approved by user!")
                    logger.warning(f"User did not gave approval for trade. {trade_variable.uuid} - Trade was not executed")
            else:
                logger.exception("Not enough Funds available. Trade not executed")
                trade_execution_check = False
                resp = ""
        else:
            logger.exception(f"{use_real_data=} has a value which is not allowed. "
                             f"Use 1 for real data and 0 for example data")
            trade_execution_check = False
            resp = ""
    # The program allows to create example trades. This is mainly for the case it should be tested and no internet is available.
    else:
        # Construct the request and return the result
        api_url = "https://api.kraken.com"
        logger.warning(f"Make a Fake Trade! Change trader_config 'make_trade' to 1 for real trades. "
                       f"Potential Call would be: {api_url},{trade_variable} "
                       f"Notice: Api key and secret not shown in log ")
        fake_response = fake_trade_response_data(trade_variable)
        logger.warning(f"Fake Trade Values: {fake_response}")
        trade_execution_check = True
        resp = fake_response
    return resp, trade_execution_check


def ask_for_order_execution(trade, make_trade, use_real_data):
    # This function allows to ask every time an order need to be executed.
    # It can be configured in the trader_config.yml

    trade_approval = int(cfg["kraken_trade"]["trade_requires_approval"])
    if trade_approval == 1:
        # Check for user approval before placing the trade in Kraken
        print(f"-----NEW TRADE-----")
        if make_trade == 1:
            print(f"Make Real Trade: True")
            if use_real_data == 1:
                print("Use Real Data: True")
            else:
                print(f"Use Real Data: {use_real_data} - Use Example Data for real Trade")
        else:
            print(f"Make Trade: {make_trade} - Execute Fake Trade")
        print("-------------------")
        trade.print_trade()
        print("-------------------")
        print(f"Should this Trade be placed to Kraken for execution. Type y/n:")
        while True:
            user_approval = input()
            if user_approval == "y":
                approved = True
                break
            elif user_approval == "n":
                approved = False
                break
            else:
                print("Wrong entry. Please enter 'y' if you approve or 'n' if you not approve:")
        return approved
    elif trade_approval == 0:
        return True
    else:
        raise RuntimeError(f"{trade_approval} is not a valid value for trade_requires_approval. Change to 0 or 1")
