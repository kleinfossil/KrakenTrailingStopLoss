def get_ohlc_json(pair, interval=1, since=0):
    # Provides Open, High, Low, Close Data. See: https://docs.kraken.com/rest/#operation/getOHLCData

    # since is currently not supported for ohlc. Therefore it will raise an error
    if since != 0:
        raise RuntimeError(f"Currently Backtest does not support 'since' in OHLC Data. Therefore this field must be '0 but it was {since}")

    # Get current active time

    # Check if I have an OHLC table for this interval

    # If not create an OHLC table based on the ts table provided

    # create a dict.
    # Load the values from the OHLC table starting with the value


    json_response = {}
    return json_response


def get_ticker(pair):
    # Gets the latest ticket
    json_response = {}
    return json_response


def get_asset_pairs(pair):
    # Gets Kraken asset Pairs
    json_response = {}
    return json_response
