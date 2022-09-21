
from dataclasses import dataclass
import time

from stoploss.report.report_position import *
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
    trigger: Decimal = 0                          # Trigger for stop loss

    last_decision_price = None

    position_number: str = f"P-{int(time.time())}"  # Position number to identify related trades

    def __post_init__(self):
        # Make the first entry into the Positions-Book after creation of a position
        book_name = "positions"
        positions_book = open_book(book_name)
        pos_dict = {
            "Position_ID": self.position_number,
            "Time": int(time.time()),
            "Current_Base_Volume": self.current_volume_of_base_currency,
            "Base_Currency": self.base_currency,
            "Current_Quote_Volume": self.current_volume_of_quote_currency,
            "Quote_Currency": self.quote_currency,
            "Trigger": self.trigger,
        }
        append_to_book(book_name, positions_book, pos_dict)

    def print_position(self):
        print(f"Current Position:")
        print(f"    Base: {self.current_volume_of_base_currency} {self.base_currency}")
        print(f"    Quote: {self.current_volume_of_quote_currency} {self.quote_currency}")
        print(f"    Trigger: {self.trigger} {self.quote_currency}")

    def add_to_position_book(self, trade):
        book_name = "positions"
        positions_book = open_book(book_name)
        pos_dict = {
            "Position_ID": self.position_number,
            "Time": trade.time_executed,
            "Current_Base_Volume": self.current_volume_of_base_currency,
            "Base_Currency": self.base_currency,
            "Current_Quote_Volume": self.current_volume_of_quote_currency,
            "Quote_Currency": self.quote_currency,
            "Trigger": self.trigger
        }
        append_to_book(book_name, positions_book, pos_dict)
