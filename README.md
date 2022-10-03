# Stop Loss Trader for Kraken
## Overview
This project implements a stop loss trader for Kraken Crypto Exchange. 
It automatically sets trigger points below or above the current price based on the traders position.
## Basic Strategy
The strategy is executed based on the current position of a trader. 
If a trader has currently no base currency (the cryptocurrency to trade) then the program will execute a buy strategy. 
If a base currency is available the program will execute a sell strategy.
### Buy Strategy
Baseline: Trader has no base currency and want to buy

Create a position and set the stop loss trigger **above** the current price. If the price gets above this trigger execute a trade and buy the base currency.
If the price moves in favor of the trader (gets lower), move the trigger price down based on the price movement (trailing stop).
If the price moves against the traders position (gets higher), keep the trigger at its position until the trigger is hit and the trade gets executed.

### Sell Strategy
Baseline: Trader has base currency and want to sell

Create a position and set the stop loss trigger **below** the current price. If the price gets below this trigger execute a trade and sell the base currency.
If the price moves in favor of the trader (gets higher), move the trigger price up based on the price movement (trailing stop).
If the price moves against the traders position (gets lower), keep the trigger at its position until the trigger is hit and the trade gets executed.


important commands
sudo journalctl -u konlet-startup