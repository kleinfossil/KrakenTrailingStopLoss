# Script functions who connect to kraken

import urllib.request
import requests
import time
import json
from stoploss.helper_scripts.helper import (
    get_logger)

logger = get_logger("stoploss_logger")


api_domain = "https://api.kraken.com"
api_path = "/0/public/"
api_data = ""


# Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData
def get_ohlc_json(pair, interval=1, since=0):

    endpoint_path = "?pair=%(pair)s&interval=%(interval)s"
    api_symbol = pair.upper()

    try:
        # create the payload by adding the api_symbol and the api_start into api_data
        api_data = endpoint_path % {"pair": api_symbol, "interval": interval}

        # Make the API request using urllib library
        logger.info("Preparing URL Request: " + api_domain + api_path + "OHLC" + api_data)
        api_request = urllib.request.Request(api_domain + api_path + "OHLC" + api_data)

        try:

            api_data = urllib.request.urlopen(api_request).read()

        except Exception as e:
            logger.exception("There was an exception calling the Kraken API.")
            logger.exception("Exception: " + str(e))
            time.sleep(3)

        api_data = json.loads(api_data)

        if len(api_data["error"]) != 0:
            logger.exception(" In the api_data was an Error.")
            time.sleep(3)
        else:
            logger.info("Kraken Request Executed and JSON Data provided")
        return api_data
    except KeyboardInterrupt:
        print("Keyboard Interrupt")



def get_ticker(pair):
    api_symbol = pair.upper()
    value = requests.get(f'https://api.kraken.com/0/public/Ticker?pair={api_symbol}').json()
    return value
