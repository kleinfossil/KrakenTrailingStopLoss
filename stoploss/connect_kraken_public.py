# Script functions who connect to kraken
import traceback
import requests
import time
from stoploss.helper_scripts.helper import (
    get_logger)

logger = get_logger("stoploss_logger")

api_domain = "https://api.kraken.com"
api_path = "/0/public/"


def make_public_data_request(api_request, request_try=3):
    logger.info(f"Preparing URL Request: {api_request}")
    request_finished = False
    request_attempts = 0
    try:
        while not request_finished:
            try:
                resp = requests.get(api_request)
                request_attempts += 1
                if resp.status_code == 200 and request_attempts < request_try:
                    request_finished = True
                    return resp
                time.sleep(3)
            except Exception as e:
                logger.error(f"{traceback.print_stack()} {e}")
        raise RuntimeError(f"The following public API Request could not be executed : {api_request}")
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


def check_response_for_errors(json_response, api_request):
    try:
        if len(json_response["error"]) != 0:
            raise RuntimeError(f"Api Request could be excuted {api_request}, but had an Error: {json_response['error']}\n"
                               f"Full Response: {json_response}")
        else:
            logger.debug("Kraken Request Executed and JSON Data provided")
            return True
    except RuntimeError as e:
        logger.error(f"{traceback.print_stack()} {e}")


# Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData
def get_ohlc_json(pair, interval=1, since=0):
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
    api_symbol = pair.upper()
    endpoint = "Ticker"

    endpoint_attribute_structure = "?pair=%(pair)s"
    endpoint_attributes = endpoint_attribute_structure % {"pair": api_symbol}

    api_request = api_domain + api_path + endpoint + endpoint_attributes
    json_response = make_public_data_request(api_request=api_request).json()
    if check_response_for_errors(json_response=json_response, api_request=api_request):
        return json_response
