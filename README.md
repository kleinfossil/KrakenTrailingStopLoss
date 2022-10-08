# Stop Loss Trader for Kraken
## Overview
This project implements a stop loss trader for Kraken Crypto Exchange. 
It automatically sets trigger points below or above the current price based on the traders position.
The strategy is also known as trailing stop.
## Business Context
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
## Developer Details
### Run the Trader
First install all requirements via "pip install -r requirements.txt".

--> environment.yml is currently not tested and Docker is not yet implemented

For the first setup you need to update the api_key files with your Kraken API key. For details see here: https://support.kraken.com/hc/en-us/articles/360000919966-How-to-create-an-API-key .

Also update the mail_info.yml with your email address or deactivate emails in the config. 

All Configuration is set up in trader_config.yml

After the setup, the program can be started by simply executing "python main.py" which already has all arguments correctly filled. Or you can start the trade_stoploss.py and include the required arguments. 
### Run the reporting Tool
The report Tool will collect all trades and create an excel sheet of all trades and closed trades. 

Execute "python report_trades.py"



