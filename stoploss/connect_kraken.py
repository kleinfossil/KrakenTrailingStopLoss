# Script functions who connect to kraken

import logging
import urllib.request
import time
import json
logger = logging.getLogger(__name__)


# Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData
def get_ohlc_json(pair, interval=1, since=0):

    api_domain = "https://api.kraken.com"
    api_path = "/0/public/"
    api_data = ""
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

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    return api_data