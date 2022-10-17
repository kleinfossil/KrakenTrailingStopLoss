import unittest
import os

# Before I can import anything from this project I need to make sure that I am working at the same directory as the function I want to test
# The following will change the working directory to \StopLoss\
dir_path = os.path.dirname(os.path.realpath(__file__))
main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"
os.chdir(main_dir_path)

from strategy_stoploss.backtest.connect_kraken_private import get_account_balance, get_open_orders
from strategy_stoploss.backtest.set_kraken_private import set_account_balance, set_open_order


class TestBacktest(unittest.TestCase):

    @unittest.skip('test_get_account_balance - Is working')
    def test_get_account_balance(self):
        response = get_account_balance("backtest")
        test_value = {'error': [], 'result': {'XETH': '0.00', 'ZEUR': '0.00'}}

        self.assertEqual(response, test_value, f"Should be: {test_value}")

        path = f"{main_dir_path}/strategy_stoploss/backtest/data/current_account_balance.pickle"
        new_balance = {'XETH': '0.85676089', 'ZEUR': '27.00'}
        set_account_balance(path=path, balance_dict=new_balance)
        test_value = {'error': [], 'result': new_balance}
        response = get_account_balance("backtest")

        self.assertEqual(response, test_value, f"Should be: {test_value}")

    def test_get_open_orders(self):
        response = get_open_orders("backtest")
        test_value = {"error": [], "result": {"open": {}}}
        self.assertEqual(response, test_value, f"Should be: {test_value}")

        path = f"{main_dir_path}/strategy_stoploss/backtest/data/current_open_orders.json"
        # Order dict structure:
        # pair, type, price, price2, vol
        new_order = {"pair": "ETHEUR", "type": "sell", "price": "1338.06", "price2": "1337.06", "vol": "0.85676089"}
        set_open_order(path=path, order_dict=new_order)
        test_value = { "error": [],
                    "result":
                        {"open":
                            {"OUN3AM-4Y5QV-UJPT7M":
                                {"refid": "None",
                                "link_id": "ONILUM-B6WBI-4HACIO",
                                "userref": "backtest",
                                "status": "open",
                                "opentm": "",
                                "starttm": "0",
                                "expiretm": "0",
                                "descr":
                                  {"pair": "ETHEUR",
                                    "type": "sell",
                                    "ordertype": "stop-loss-limit",
                                    "price": "1338.06",
                                    "price2": "1337.06",
                                    "leverage": "none",
                                    "order": "",
                                    "close": ""},
                                "vol": "0.85676089",
                                "vol_exec": "0.00000000",
                                "cost": "0.00000",
                                "fee": "0.00000",
                                "price": "0.00000",
                                "stopprice": "0.00000",
                                "limitprice": "0.00000",
                                "misc": "",
                                "oflags": "fciq"}}}}
        response = get_open_orders("backtest")

        self.assertEqual(response, test_value, f"Should be: {test_value}")


    @classmethod
    def tearDownClass(cls):
        # clean_up(f"{main_dir_path}/strategy_stoploss/backtest/data/current_account_balance.pickle")
        # clean_up(f"{main_dir_path}/strategy_stoploss/backtest/data/current_open_orders.pickle")
        print("done")


def clean_up(path):
    try:
        os.remove(path)
    except FileNotFoundError as e:
        print(e)
        pass


if __name__ == '__main__':
    unittest.main()

