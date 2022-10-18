# Script functions who connect to kraken public data (no secret required)
import traceback
import requests
import time
from strategy_stoploss.helper_scripts.helper import (
    get_logger)
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)

logger = get_logger("stoploss_logger")

api_domain = "https://api.kraken.com"
api_path = "/0/public/"


def make_public_data_request(api_request, request_try=int(cfg["kraken_trade"]["max_retries_error_requests"])):
    # Creates a public data request. Sometimes the data is not provided immediately. In this case it tries 3 times.

    logger.info(f"Preparing URL Public Request: {api_request}")
    request_finished = False
    request_attempts = 1
    sleeping_counter = int(cfg["kraken_trade"]["sleep_time_between_error_requests"])
    try:
        while (not request_finished) and (request_attempts <= request_try):
            try:
                resp = requests.get(api_request)

                if resp.status_code == 200:
                    request_finished = True
                    return resp
            except Exception as e:
                logger.error(f"Public Data Request - {request_attempts=}  <= {request_try=}\n"
                             f"{traceback.print_stack()} {e}")
            request_attempts += 1
            time.sleep(sleeping_counter)
            sleeping_counter += 10
        raise RuntimeError(f"The following public API Request could not be executed : {api_request}")
    except RuntimeError as e:
        logger.error(f"Public Request failed. {traceback.print_stack()} {e}")


def check_response_for_errors(json_response, api_request):
    # Checks if the Kraken response (the content) had any error

    try:
        if len(json_response["error"]) != 0:
            raise RuntimeError(f"Api Request could be excuted {api_request}, but had an Error: {json_response['error']}\n"
                               f"Full Response: {json_response}")
        else:
            logger.debug("Kraken Request Executed and JSON Data provided")
            return True
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def get_ohlc_json(pair, interval=1, since=0):
    # Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData
    api_symbol = pair.upper()
    endpoint = "OHLC"

    endpoint_attribute_structure = "?pair=%(pair)s&interval=%(interval)s"
    endpoint_attributes = endpoint_attribute_structure % {"pair": api_symbol, "interval": interval}

    api_request = api_domain + api_path + endpoint + endpoint_attributes
    api_response = make_public_data_request(api_request)
    json_response = api_response.json()
    if check_response_for_errors(json_response=json_response, api_request=api_request):
        return json_response


def get_ticker(pair):
    # Gets the latest ticket
    api_symbol = pair.upper()
    endpoint = "Ticker"

    endpoint_attribute_structure = "?pair=%(pair)s"
    endpoint_attributes = endpoint_attribute_structure % {"pair": api_symbol}

    api_request = api_domain + api_path + endpoint + endpoint_attributes
    json_response = make_public_data_request(api_request=api_request).json()
    if check_response_for_errors(json_response=json_response, api_request=api_request):
        return json_response


def get_asset_pairs(pair):
    # Gets Kraken asset Pairs
    api_symbol = pair.upper()
    endpoint = "AssetPairs"

    endpoint_attribute_structure = "?pair=%(pair)s"
    endpoint_attributes = endpoint_attribute_structure % {"pair": api_symbol}

    api_request = api_domain + api_path + endpoint + endpoint_attributes
    json_response = make_public_data_request(api_request=api_request).json()
    if check_response_for_errors(json_response=json_response, api_request=api_request):
        return json_response
