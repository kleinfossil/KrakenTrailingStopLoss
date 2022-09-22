import traceback

from stoploss.helper_scripts.helper import get_logger
from stoploss.helper_scripts.google_secretmanager import access_secret_version
import os
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
        match key_type:
            case "query":
                key = "query-key"
            case "create":
                key = "create-cancel"
            case "cancel":
                key = "create-cancel"
            case "modify":
                key = "modify"
            case _:
                raise RuntimeError(f"'{key_type}' is not a known key")

        google_secrets = int(cfg["kraken_private"]["google"]["google-secrets"])
        if google_secrets == 1:
            logger.debug("Get Query API Keys from Google")
            kraken_api_key = access_secret_version("250571186544", "KRAKEN_API_KEY", "latest")
            kraken_private_key = access_secret_version("250571186544", "KRAKEN_API_PRIVATE_KEY", "latest")
        elif google_secrets == 0:
            logger.warning("Get Query API Keys from local yaml file. This is for development only. Use Google Secrets for production runs. "
                           "Change trader_config to google-secrets=1")
            local_yaml_key_location = cfg["kraken_private"]["development-keys"]["key-location"]
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
        req = requests.post((api_url + uri_path), headers=headers, data=data)
    except RuntimeError as err:
        logger.error(f"The Request to Kraken was not successful. "
                     f"The following was called without secrets {api_url}{uri_path}{data} "
                     f"The Error was {err=}, {type(err)=}")
        raise RuntimeError("Kraken Request was not executed. Read Logs for details.")
    return req


# Get the current account balance
def get_account_balance(key_type):
    endpoint = "Balance"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time()))
    }, api_key, api_sec)
    return resp.json()


# Get open Orders
def get_open_orders(key_type):
    endpoint = "OpenOrders"
    api_key, api_sec = get_secrets(key_type=key_type, version=cfg["kraken_private"]["development_keys"]["key_version"])  # Read Kraken API key and secret stored in environment variables
    # Construct the request and return the result
    resp = kraken_request(api_domain, f'{api_path}{endpoint}', {
        "nonce": str(int(1000 * time.time())),
        "trades": True
    }, api_key, api_sec)
    logger.info(f"Open Orders received from Kraken. Orders: {str(resp.json())}")
    return resp.json()
