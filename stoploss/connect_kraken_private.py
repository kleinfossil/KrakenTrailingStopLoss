# This script manages all functions required for a private connections to kraken. Means all connections which require secrets.

import traceback

from stoploss.helper_scripts.helper import get_logger
from test.fake_data.fake_data_user import fake_response_query_data
from stoploss.data_classes.global_data import get_google_secret
import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)
logger = get_logger("stoploss_logger")

api_domain = "https://api.kraken.com"
api_path = "/0/private/"


def get_secrets(key_type, version):
    # Read Kraken API key and secret for query stored in Google or environment variable (for testing)

    try:
        # The match case was actually developed to manage different secrets per request.
        # As google just allows 10.000 requests per month I reduced the keys for google to one.
        match key_type:
            case "query":
                key = "query-key"
            case "trade":
                key = "create-cancel"
            case "cancel":
                key = "create-cancel"
            case "modify":
                key = "modify"
            case "google":
                key = "google"
            case _:
                raise RuntimeError(f"'{key_type}' is not a known key")

        google_secrets = int(cfg["kraken_private"]["google"]["google-secrets"])
        if google_secrets == 1:
            logger.debug("Get Query API Keys from Google")
            secret_dict = get_google_secret()
            kraken_api_key = secret_dict["key"]
            kraken_private_key = secret_dict["sec"]

        elif google_secrets == 0:
            logger.warning("Get Query API Keys from local yaml file. This is for development only. Use Google Secrets for production runs. "
                           "Change trader_config to google-secrets=1")
            local_yaml_key_location = cfg["kraken_private"]["development_keys"]["key_location"]
            with open(local_yaml_key_location, "r") as key_yml:
                key_cfg = yaml.load(key_yml, Loader=SafeLoader)
            kraken_api_key = key_cfg["kraken-key"][key][version]["key"]
            kraken_private_key = key_cfg["kraken-key"][key][version]["sec"]
        else:
            logger.error("Google Secrets are not configured correctly. Use either 1 for google secrets or 0 for local secrets")
            raise RuntimeError("Google Secrets are not configured correctly. Use either 1 for google secrets or 0 for local secrets")
        return kraken_api_key, kraken_private_key
    except RuntimeError as e:
        logger.error(traceback.print_stack(), e)


def get_kraken_signature(urlpath, data, secret):
    # See https://docs.kraken.com/rest/#section/Authentication/Headers-and-Signature

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def kraken_request(api_url, uri_path, data, api_key, api_sec):
    # Attaches auth headers and returns results of a POST request
    # get_kraken_signature() as defined in the 'Authentication' section
    headers = {'API-Key': api_key, 'API-Sign': get_kraken_signature(uri_path, data, api_sec)}


    try:
        logger.info(f"Preparing URL Private Request: {api_url}{uri_path}{data}")
        req = requests.post((api_url + uri_path), headers=headers, data=data)
    except RuntimeError as err:
        logger.error(f"The Request to Kraken was not successful. "
                     f"The following was called without secrets {api_url}{uri_path}{data} "
                     f"The Error was {err=}, {type(err)=}")
        raise RuntimeError("Kraken Request was not executed. Read Logs for details.")
    return req


def get_account_balance(key_type):
    # Get the current account balance

    endpoint = "Balance"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time()))
    }, api_key, api_sec)
    return resp.json()


def get_open_orders(key_type):
    # Get open Orders

    endpoint = "OpenOrders"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time())),
        "trades": True
    }, api_key, api_sec)
    logger.debug(f"Open Orders received from Kraken. Orders: {str(resp.json())}")
    return resp.json()


def get_closed_orders(key_type, till=""):
    # Get Closed Orders

    endpoint = "ClosedOrders"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    if till != "":
        resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
            "nonce": str(int(1000 * time.time())),
            "trades": True,
            "end": till
        }, api_key, api_sec)
    else:
        resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
            "nonce": str(int(1000 * time.time())),
            "trades": True,
        }, api_key, api_sec)
    logger.debug(f"Closed Orders received from Kraken. Orders: {str(resp.json())}")
    return resp.json()


def get_trades_history(key_type):
    # Get Trades History.

    endpoint = "TradesHistory"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time())),
        "trades": True
    }, api_key, api_sec)
    logger.debug(f"Trades History Received from Kraken. Trades: {str(resp.json())}")
    return resp.json()


def get_trade(txid, key_type):
    # Get current trades.

    endpoint = "QueryTrades"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time())),
        "txid": txid,
        "trades": True
    }, api_key, api_sec)
    logger.debug(f"Specific Information about a Trade received from Kraken. Trade Details: {str(resp.json())}")
    return resp.json()


def query_order_info(txid, key_type):
    # Retrieve information about specific orders.

    endpoint = "QueryOrders"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables

    make_query = int(cfg["debugging"]["kraken"]["make_real_query"])

    if make_query == 1:
        resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
            "nonce": str(int(1000 * time.time())),
            "txid": txid,                        # Comma delimited list of transaction IDs to query info about (20 maximum)
            "trades": True
        }, api_key, api_sec)
        return resp.json()
    else:
        logger.warning(f"Make a Fake Trade Query! Change main_config 'MakeRealQuery' to 1 for real queries. "
                       f"Notice: Api key and secret not shown in log ")
        fake_response = fake_response_query_data(txid)
        logger.warning(f"Fake Query Values: {fake_response}")
        resp = fake_response
        return resp


def trade_add_order(trade_dict, key_type):
    # Creates a new order on kraken

    endpoint = "AddOrder"
    version = cfg["kraken_private"]["development_keys"]["key_version"]
    api_key, api_sec = get_secrets(key_type=key_type, version=version)  # Read Kraken API key and secret stored in environment variables
    kill_switch = cfg["debugging"]["kraken"]["kill_switch"]
    if kill_switch == "do_not_trade":
        logger.warning(f"Kill switch is {kill_switch}. No trades will be made")
        resp = {}
    elif kill_switch == "trade":
        logger.debug(f"Make request to kraken with following Data: {trade_dict}")
        resp = kraken_request(api_domain, f'{api_path}{endpoint}', trade_dict, api_key, api_sec)
    else:
        raise RuntimeError(f"{kill_switch=} is not set correctly")
    trade_execution_check = True
    logger.debug(f"Trade send to Kraken. Response was: \n"
                 f"{resp}\n"
                 f"{resp.json()}")
    return resp.json(), trade_execution_check


def did_order_change(trade_dict):
    # This is related to trade_edit_order.
    # Checks if the new order is actually changing. If not then there is no need to update the order

    open_order = get_open_orders("query")
    logger.debug("Check if the market order and the new order is the same")
    logger.debug(f"Open Order recived from Kraken: {open_order}")
    logger.debug(f"Planned Order to be executed: {trade_dict}")
    changed_dict = {"changed": True}
    try:
        active_transaction = open_order["result"]["open"][trade_dict["txid"]]
    except KeyError:
        logger.error(traceback.print_stack(), f"{trade_dict['txid']} Transaction ID does not exists on Kraken. There is no Order which can be edited.")
        exit(1)
    if open_order["result"]["open"][trade_dict["txid"]]["status"] == "open":
        if (trade_dict["pair"] == "XETHZEUR") and (open_order["result"]["open"][trade_dict["txid"]]["descr"]["pair"] == "ETHEUR"):
            if trade_dict["type"] == open_order["result"]["open"][trade_dict["txid"]]["descr"]["type"]:
                if trade_dict["price"] == open_order["result"]["open"][trade_dict["txid"]]["descr"]["price"]:
                    if trade_dict["price2"] == open_order["result"]["open"][trade_dict["txid"]]["descr"]["price2"]:
                        if trade_dict["volume"] == open_order["result"]["open"][trade_dict["txid"]]["vol"]:
                            changed_dict["changed"] = False

    changed_dict['current'] = open_order
    changed_dict['new'] = trade_dict

    return changed_dict


def trade_edit_order(trade_dict, key_type):
    # Edits a Order

    endpoint = "EditOrder"
    version = cfg["kraken_private"]["development_keys"]["key_version"]
    api_key, api_sec = get_secrets(key_type=key_type, version=version)  # Read Kraken API key and secret stored in environment variables
    kill_switch = cfg["debugging"]["kraken"]["kill_switch"]
    if kill_switch == "do_not_trade":
        logger.warning(f"Kill switch is {kill_switch}. No trades will be made")
        resp = ""
    elif kill_switch == "trade":
        logger.debug(f"Make request to kraken with following Data: {trade_dict}")
        changed_dict = did_order_change(trade_dict)
        if changed_dict["changed"]:
            resp = kraken_request(api_domain, f'{api_path}{endpoint}', trade_dict, api_key, api_sec)
        else:
            print(f"Order is the same as an existing on Kraken. Order not send to Kraken\n"
                  f"Current Order: {changed_dict['current']}\n"
                  f"New Order: {changed_dict['new']}")
            resp = ""
    else:
        raise RuntimeError(f"{kill_switch=} is not set correctly")
    trade_execution_check = True
    if resp == "":
        logger.debug(f"Kill Switch Active or Order didn't change")
        return resp, trade_execution_check
    else:
        logger.debug(f"Edit Trade send to Kraken. Response was: \n"
                     f"{resp}\n"
                     f"{resp.json()}")
        return resp.json(), trade_execution_check


