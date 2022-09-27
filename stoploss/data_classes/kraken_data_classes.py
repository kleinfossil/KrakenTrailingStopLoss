from dataclasses import dataclass
import time
from uuid import uuid4


@dataclass
class AddTrade:
    trade_type: str = "AddTrade"                # The name of this dataclass
    uuid: uuid4 = uuid4().hex
    nonce: str = str(int(time.time()))   # User Signed API header. Must be always increasing number
    userref: str = ""                           # Optional User Reference. Must be Int32!
    ordertype: str = ""                         # market, limit, stop-loss, take-profit, stop-loss-limit,
                                                # take-profit-limit, settle-position
    type: str = ""                              # buy, sell
    volume: str = ""                            # Order quantity in terms of the base asset
    pair: str = ""                              # Asset Pair
    price: str = ""                             # Asset Price. in Quote Currency Limit price for Limit orders/ Trigger price
                                                # for stop-loss, stop-loss-limit,
                                                # take-profit and take-profit-limit
    price2: str = ""                            # Limit price for stop-loss-limit
                                                # and take-profit-limit orders. Price2 can be set as an
                                                # offset. See https://docs.kraken.com/rest/#operation/addOrder
    leverage: str = ""                          # Amount of leverage desired (default = none)
    oflags: str = ""                            # Comma delimited list of order flags
                                                # post post-only order (available when ordertype = limit)
                                                # fcib prefer fee in base currency (default if selling)
                                                # fciq prefer fee in quote currency (default if buying,
                                                # mutually exclusive with fcib)
                                                # nompp disable market price protection for market orders
    timeinforce: str = ""                       # GTC (Good-'til-cancelled - default),
                                                # IOC (immediate-or-cancel),
                                                # GTD (good-'til-date - requires expiremt)
    startm: str = ""                            # 0 = now, can also a include a unix timestamp or an offset
    expiretm: str = ""                          # 0 = now, can also a include a unix timestamp or an offset
    deadline: str = ""                          # requires more code. See: https://stackoverflow.com/questions/100210/what-is-the-standard-way-to-add-n-seconds-to-datetime-time-in-python/100345
    validate: str = ""                          # Validates input only if true

    # Following Values can be set after a trade was executed
    txid_response: str = ""                              # Transaction ID, can be set as soon as the transaction was executed
    executed: str = "False"                     # Was the Transaction executed
    time_executed: str = ""                     # Time when the transaction was executed
    kraken_description: str = ""                # Description from Kraken received in the response

    def set_example_values(self, timeinforce="", expiretm="0"):
        self.nonce = str(int(time.time()))
        self.userref = "90001000"
        self.ordertype = "stop-loss-limit"
        self.type = "buy"
        self.volume = "0.01"
        self.pair = "XETHZEUR"
        self.price = "10"
        self.price2 = "11"
        self.timeinforce = timeinforce
        self.expiretm = expiretm
        self.validate = "false"

    def as_dict(self):
        # returns the class attributes as a dictionary
        asdict = {}
        for attribute in dir(self):
            if not attribute.startswith('__') and not callable(getattr(self, attribute)):
                value = getattr(self, attribute, None)
                if value != "":
                    asdict[attribute] = value
        return asdict

    def print_trade(self):
        for attribute in dir(self):
            if not attribute.startswith('__') and not callable(getattr(self, attribute)):
                value = getattr(self, attribute, None)
                if value != "":
                    print(f"{attribute}: {value}")


@dataclass
class EditOrder:
    trade_type: str = "EditOrder"               # The name of this dataclass
    uuid: uuid4 = uuid4().hex                   # Internal ID
    nonce: str = str(int(time.time())*1000)          # User Signed API header. Must be always increasing number
    userref: str = ""                           # Optional User Reference. Must be Int32!
    txid: str = ""                               # Original Order ID or User Reference ID. If user reference is not unique, request will be denied.
    # ordertype: str = ""                         # market, limit, stop-loss, take-profit, stop-loss-limit,
                                                # take-profit-limit, settle-position
    type: str = ""                              # buy, sell
    volume: str = ""                            # Order quantity in terms of the base asset
    pair: str = ""                              # Asset Pair
    price: str = ""                             # Asset Price. in Quote Currency Limit price for Limit orders/ Trigger price
                                                # for stop-loss, stop-loss-limit,
                                                # take-profit and take-profit-limit
    price2: str = ""                            # Limit price for stop-loss-limit
                                                # and take-profit-limit orders. Price2 can be set as an
                                                # offset. See https://docs.kraken.com/rest/#operation/addOrder
    # leverage: str = ""                          # Amount of leverage desired (default = none)
    oflags: str = ""                            # Comma delimited list of order flags
                                                # post post-only order (available when ordertype = limit)
                                                # fcib prefer fee in base currency (default if selling)
                                                # fciq prefer fee in quote currency (default if buying,
                                                # mutually exclusive with fcib)
                                                # nompp disable market price protection for market orders
    # timeinforce: str = ""                       # GTC (Good-'til-cancelled - default),
                                                # IOC (immediate-or-cancel),
                                                # GTD (good-'til-date - requires expiremt)
    # startm: str = ""                            # 0 = now, can also a include a unix timestamp or an offset
    # expiretm: str = ""                          # 0 = now, can also a include a unix timestamp or an offset
    deadline: str = ""                          # requires more code. See: https://stackoverflow.com/questions/100210/what-is-the-standard-way-to-add-n-seconds-to-datetime-time-in-python/100345
    validate: str = ""                          # Validates input only if true

    # Following Values can be set after a trade was executed
    txid_response: str = ""                              # Transaction ID, can be set as soon as the transaction was executed
    executed: str = "False"                     # Was the Transaction executed
    time_executed: str = ""                     # Time when the transaction was executed
    kraken_description: str = ""                # Description from Kraken received in the response

    def set_example_values(self, timeinforce="", expiretm="0"):
        self.nonce = str(int(time.time()))
        self.userref = "90001000"
        self.txid = "OHVFK7-BF5HY-PHECAP"
        # self.ordertype = "stop-loss-limit"
        self.type = "buy"
        self.volume = "0.01"
        self.pair = "XETHZEUR"
        self.price = "10"
        self.price2 = "11"
        # self.timeinforce = timeinforce
        # self.expiretm = expiretm
        self.validate = "false"

    def as_dict(self):
        # returns the class attributes as a dictionary
        asdict = {}
        for attribute in dir(self):
            if not attribute.startswith('__') and not callable(getattr(self, attribute)):
                value = getattr(self, attribute, None)
                if value != "":
                    asdict[attribute] = value
        return asdict

    def print_trade(self):
        for attribute in dir(self):
            if not attribute.startswith('__') and not callable(getattr(self, attribute)):
                value = getattr(self, attribute, None)
                if value != "":
                    print(f"{attribute}: {value}")
