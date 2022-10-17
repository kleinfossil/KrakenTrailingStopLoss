# This script manages the google secret manager connection.

from google.cloud import secretmanager
from strategy_stoploss.helper_scripts.helper import get_logger
import yaml
from yaml.loader import SafeLoader

with open("trader_config.yml", "r") as yml_file:
    cfg = yaml.load(yml_file, Loader=SafeLoader)
logger = get_logger("stoploss_logger")


def get_key_and_secret_from_google():
    google_secret = {"key": access_secret_version(cfg["kraken_private"]["google"]["google-project-id"],
                                                  cfg["kraken_private"]["google"]["google-key-name"],
                                                  cfg["kraken_private"]["google"]["google-secret-version"]),
                     "sec": access_secret_version(cfg["kraken_private"]["google"]["google-project-id"],
                                                  cfg["kraken_private"]["google"]["google-sec-name"],
                                                  cfg["kraken_private"]["google"]["google-secret-version"])}
    return google_secret


def access_secret_version(project_id, secret_id, version_id):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    For More details see: https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#secretmanager-access-secret-version-python
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")

        return payload
    except RuntimeError as err:
        logger.error(f"Access to Google Secret Manager created a failure. The Error was {err=}, {type(err)=}")
