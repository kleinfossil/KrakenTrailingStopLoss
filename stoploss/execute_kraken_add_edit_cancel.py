from stoploss.helper_scripts.helper import get_logger
from connect_kraken_private import get_secrets
from checks_kraken import check_order
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")


def execute_order(trade_variable):
    # Place a new Order
    # See: https://docs.kraken.com/rest/#operation/addOrder

    # Construct the request and return the result
    api_url = "https://api.kraken.com"

    make_trade = int(cfg["debugging"]["kraken"]["make_trade"])
    use_real_data = int(cfg["debugging"]["kraken"]["use_real_trading_data"])
    resp = {}
    data = trade_variable.as_dict()
    if int(cfg["kraken_trade"]["trade_requires_approval"] == 1):
        user_approval = ask_for_order_execution(trade=trade_variable, make_trade=make_trade, use_real_data=use_real_data)
    else:
        user_approval = True

    if user_approval:
        if make_trade == 1:
            if use_real_data == 1:
                if check_order(trade_variable):
                    api_key, api_sec = get_secrets(key_type="trade", version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
                    logger.info(f"Executing Order on Kraken. Call: {api_url},{data} "
                                f"Notice: Api key and secret not shown in log")
                    # resp = kraken_request(api_url, '/0/private/AddOrder', data, api_key, api_sec)
                    trade_execution_check = True
                else:
                    logger.exception("Not enough Funds available. Trade not executed")
                    trade_execution_check = False
                    resp = ""
            elif use_real_data == 0:
                api_key, api_sec = get_secrets(key_type="trade", version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
                logger.warning("Make a Example Trade! Change main_config 'UseRealData' to 1 for real data")
                logger.warning("Overwriting trade_variables with example data")
                trade_variable.set_example_values()
                if check_order(trade_variable):
                    logger.warning(f"Executing Order on Kraken with example Data. Call: {api_url},{data} "
                                   f"Notice: Api key and secret not shown in log")
                    # resp = kraken_request(api_url, '/0/private/AddOrder', data, api_key, api_sec)
                    trade_execution_check = True
                else:
                    logger.exception("Not enough Funds available. Trade not executed")
                    trade_execution_check = False
                    resp = ""
            else:
                logger.exception(f"{use_real_data=} has a value which is not allowed. "
                                 f"Use 1 for real data and 0 for example data")
                trade_execution_check = False
                resp = ""
        else:
            logger.warning(f"Make a Fake Trade! Change trader_config 'make_trade' to 1 for real trades. "
                           f"Potential Call would be: {api_url},{trade_variable} "
                           f"Notice: Api key and secret not shown in log ")
            fake_response = fake_trade_response_data(trade_variable)
            logger.warning(f"Fake Trade Values: {fake_response}")
            trade_execution_check = True
            resp = fake_response
    else:
        trade_execution_check = False
        print(f"Trade was not approved by user!")
        logger.warning(f"User did not gave approval for trade. {trade_variable.uuid} - Trade was not executed")
    return resp, trade_execution_check


def ask_for_order_execution(trade, make_trade, use_real_data):
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
