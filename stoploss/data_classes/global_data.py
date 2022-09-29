import keyring


def set_google_secret(secret_dict):
    keyring.set_password("google", "key", secret_dict["key"])
    keyring.set_password("google", "sec", secret_dict["sec"])


def get_google_secret():
    secret_dict = {"key": keyring.get_password("google", "key"),
                   "sec": keyring.get_password("google", "sec")}
    return secret_dict


