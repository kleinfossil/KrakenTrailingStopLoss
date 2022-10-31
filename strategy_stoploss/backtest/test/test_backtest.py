import unittest
import os

# Before I can import anything from this project I need to make sure that I am working at the same directory as the function I want to test
# The following will change the working directory to \StopLoss\
dir_path = os.path.dirname(os.path.realpath(__file__))
main_dir_path = f"{dir_path.split('StopLoss')[0]}StopLoss"
os.chdir(main_dir_path)

from strategy_stoploss.backtest.connect_kraken_private import get_account_balance, get_open_orders, trade_add_order, trade_edit_order
from strategy_stoploss.backtest.set_kraken_private import set_account_balance, set_open_order


class TestBacktest(unittest.TestCase):

    # @unittest.skip('test_get_account_balance - Is not tested')
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

    # @unittest.skip('test_get_open_orders - Is not tested')
    def test_get_open_orders(self):
        response = get_open_orders("backtest")
        test_value = {"error": [], "result": {"open": {}}}
        self.assertEqual(response, test_value, f"Should be: {test_value}")

        path = f"{main_dir_path}/strategy_stoploss/backtest/data/current_open_orders.json"
        # Order dict structure:
        # pair, type, price, price2, vol
        new_order = {"pair": "ETHEUR", "type": "sell", "price": "1338.06", "price2": "1337.06", "volume": "0.85676089"}
        set_open_order(path=path, order_dict=new_order)
        test_value = { "error": [],
                    "result":
                        {"open":
                            {"KAS3AM-4Y5QV-UJPT7M":
                                {"refid": "None",
                                "link_id": "KASLUM-B6WBI-4HACIO",
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

    # @unittest.skip('test_trade_add_order - Is not tested')
    def test_trade_add_order(self):
        # Tests will check if a new trade_dict provided to trade_add_order will update the current_open_orders.json

        # Now update the trade with a new trade_dict
        trade_dict = {
            'executed': 'False',
            'nonce': '1667201316000',
            'ordertype': 'stop-loss-limit',
            'pair': 'XETHZEUR',
            'price': '1601.80',
            'price2': '1602.80',
            'timeinforce': 'GTC',
            'trade_type': 'AddTrade',
            'type': 'buy',
            'userref': 1667201314,
            'uuid': '64f06ce30607438795df9e0f0f69f21b',
            'validate': 'true',
            'volume': '0.74590055'
        }

        test_value_after = {
            "error": [],
            "result": {
                "open": {
                    "KAS3AM-4Y5QV-UJPT7M": {
                        "refid": "None",
                        "link_id": "KASLUM-B6WBI-4HACIO",
                        "userref": "backtest",
                        "status": "open",
                        "opentm": "",
                        "starttm": "0",
                        "expiretm": "0",
                        "descr": {
                            "pair": "ETHEUR",
                            "type": "buy",
                            "ordertype": "stop-loss-limit",
                            "price": "1601.80",
                            "price2": "1602.80",
                            "leverage": "none",
                            "order": "",
                            "close": ""
                        },
                        "vol": "0.74590055",
                        "vol_exec": "0.00000000",
                        "cost": "0.00000",
                        "fee": "0.00000",
                        "price": "0.00000",
                        "stopprice": "0.00000",
                        "limitprice": "0.00000",
                        "misc": "",
                        "oflags": "fciq"
                    }
                }
            }
        }

        trade_response, trade_check = trade_add_order(trade_dict=trade_dict, key_type="backtest")
        # check if the trade_add_order response is the same as the test value
        self.assertEqual(trade_response, test_value_after, f"Should be: {test_value_after}")

        # check if the open orders provide the same value
        open_orders_response = get_open_orders("backtest")
        self.assertEqual(open_orders_response, trade_response, f"Should be: {trade_response}")

    def test_trade_edit_order(self):
        # Tests will check if a new trade_dict provided to trade_add_order will update the current_open_orders.json

        # Now update the trade with a new trade_dict
        trade_dict = {
            'executed': 'False',
            'nonce': '1667201316000',
            'ordertype': 'stop-loss-limit',
            'pair': 'XETHZEUR',
            'price': '1603.80',
            'price2': '1604.80',
            'timeinforce': 'GTC',
            'trade_type': 'AddTrade',
            'type': 'buy',
            'userref': 1667201314,
            'uuid': '64f06ce30607438795df9e0f0f69f21b',
            'validate': 'true',
            'volume': '0.84590055'
        }

        test_value_after = {
            "error": [],
            "result": {
                "open": {
                    "KAS3AM-4Y5QV-UJPT7M": {
                        "refid": "None",
                        "link_id": "KASLUM-B6WBI-4HACIO",
                        "userref": "backtest",
                        "status": "open",
                        "opentm": "",
                        "starttm": "0",
                        "expiretm": "0",
                        "descr": {
                            "pair": "ETHEUR",
                            "type": "buy",
                            "ordertype": "stop-loss-limit",
                            "price": "1603.80",
                            "price2": "1604.80",
                            "leverage": "none",
                            "order": "",
                            "close": ""
                        },
                        "vol": "0.84590055",
                        "vol_exec": "0.00000000",
                        "cost": "0.00000",
                        "fee": "0.00000",
                        "price": "0.00000",
                        "stopprice": "0.00000",
                        "limitprice": "0.00000",
                        "misc": "",
                        "oflags": "fciq"
                    }
                }
            }
        }

        trade_response, trade_check = trade_edit_order(trade_dict=trade_dict, key_type="backtest")
        # check if the trade_add_order response is the same as the test value
        self.assertEqual(trade_response, test_value_after, f"Should be: {test_value_after}")

        # check if the open orders provide the same value
        open_orders_response = get_open_orders("backtest")
        self.assertEqual(open_orders_response, trade_response, f"Should be: {trade_response}")

    @classmethod
    def tearDownClass(cls):
        clean_up(f"{main_dir_path}/strategy_stoploss/backtest/data/current_account_balance.pickle")
        clean_up(f"{main_dir_path}/strategy_stoploss/backtest/data/current_open_orders.json")
        print("done")


def clean_up(path):
    try:
        os.remove(path)
    except FileNotFoundError as e:
        print(e)
        pass


if __name__ == '__main__':
    unittest.main()

