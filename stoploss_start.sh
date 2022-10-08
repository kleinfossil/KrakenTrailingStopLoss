#!/bin/sh

# This script is planned to manage the trader with a cronjob

printf "$(date): [---STOP LOSS START---]\n">> ~/Apps/Raw/221003_Kraken_trader/crontab_logs/kraken_cronjob_log.log
python main.py
printf "[---STOP LOSS FINISH---]\n">> ~/Apps/Raw/221003_Kraken_trader/crontab_logs/kraken_cronjob_log.log
exit 0
