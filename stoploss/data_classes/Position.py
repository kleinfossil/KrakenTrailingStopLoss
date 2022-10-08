
from dataclasses import dataclass
import time

from stoploss.helper_scripts.helper import convert_unix_time_to_datetime
from stoploss.report.manage_books import *
from decimal import Decimal


@dataclass
class Position:
    # A position of a trader is represented of the assets a trader holds.
    # E.g. if a trader holds a large amount of base currency then the trader is long
    # expecting the base currency to raise.
    # If a trader holds a large amount of quote currency then the trader is short and expects the base currency to fall.

    base_currency: str                          # Currency code for trading. E.g. ETH
    quote_currency: str                         # Currency which is used for valuing the base currency. E.g. EUR
    exchange_currency_pair: str                 # Currency pair for the position. e.g. XETHZEUR.
                                                # Used for easier interaction with the exchange platform
    current_volume_of_base_currency: Decimal      # Current volume of base currency. e.g. 100
    current_volume_of_quote_currency: Decimal     # Current volume of quote currency. e.g. 0.01
    position_number: int = 0                    # Position number to identify related trades
    trigger: Decimal = 0                        # Trigger for stop loss

    # Stop Loss strategy values
    current_std: Decimal = 0                    # Current standard deviation
    current_high: Decimal = 0                   # Current high price the position is traded with
    current_low: Decimal = 0                    # Current low price the position is traded with
    current_trade_price: Decimal = 0            # Current Trade price

    def __post_init__(self):
        # Make the first entry into the Positions-Book after creation of a position
        self.position_number = int(time.time())
        book_name = "positions"
        open_book(book_name)

    def print_position(self):
        print(f"Current Trader Position before Trade:")
        print(f"    Base: {self.current_volume_of_base_currency} {self.base_currency}")
        print(f"    Quote: {self.current_volume_of_quote_currency} {self.quote_currency}")
        print(f"    Trigger: {self.trigger} {self.quote_currency}")

    def add_to_position_book(self):
        book_entry_time = time.time()
        book_name = "positions"
        positions_book = open_book(book_name)
        pos_dict = {
            "Position_ID": self.position_number,
            "Time": convert_unix_time_to_datetime(book_entry_time),
            "Current_Base_Volume": self.current_volume_of_base_currency,
            "Base_Currency": self.base_currency,
            "Current_Quote_Volume": self.current_volume_of_quote_currency,
            "Quote_Currency": self.quote_currency,
            "Trigger": self.trigger,
            "Last_Low": self.current_low,
            "Last_High": self.current_high,
            "Last_std": self.current_std,
            "Last_Trade_Price": self.current_trade_price
        }
        append_to_book(book_name, positions_book, pos_dict)


@dataclass
class Order:
    txid: str
    base_currency: str  # Currency code for trading. E.g. ETH
    quote_currency: str  # Currency which is used for valuing the base currency. E.g. EUR
    exchange_currency_pair: str
    price: Decimal
    price2: Decimal
    volume_base: Decimal
    volume_quote: Decimal

