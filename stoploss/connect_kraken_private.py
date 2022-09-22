from stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader
with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)
logger = get_logger("stoploss_logger")


def get_secrets_query_on_google():
    # Read Kraken API key and secret for query stored in Google or environment variable (for testing)
    google_secrets = int(cfg["kraken_private"]["google"]["secrets"])
    if google_secrets == 1:
        logger.info("Get Query API Keys from Google")
        kraken_api_key = access_secret_version("250571186544", "KRAKEN_API_KEY", "latest")
        kraken_private_key = access_secret_version("250571186544", "KRAKEN_API_PRIVATE_KEY", "latest")
    elif google_secrets == 0:
        logger.warning("Get Query API Keys from Environment Variable. Use Google Keys for production runs. "
                       "Change main_config to GoogleSecrets=1")
        kraken_api_key = os.environ["KRAKEN_API_KEY"]
        kraken_private_key = os.environ["KRAKEN_API_PRIVATE_KEY"]
    else:
        logger.exception("Secret Keys could not be assigned")
        raise RuntimeError("Could not find a secret")
    return kraken_api_key, kraken_private_key


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


def get_account_balance():
    # Get the current account balance

    api_key, api_sec = get_secrets_query_on_google()  # Read Kraken API key and secret stored in environment variables

    # Construct the request and return the result
    api_url = "https://api.kraken.com"
    resp = kraken_request(api_url, '/0/private/Balance', {
        "nonce": str(int(1000 * time.time()))
    }, api_key, api_sec)
    return resp.json()