from wserver import Wserver
from toolkit.kokoo import timer
from constants import logging
from traceback import print_exc


class Helper:

    completed_trades = []
    subscribed = {}
    _api = None
    _ws = None

    @classmethod
    def api(cls, api):
        try:
            cls._api = api
            cls._ws = Wserver(api.kite)
        except Exception as e:
            logging.error(f"api {e}")

    @classmethod
    def _subscribe_till_ltp(cls, ws_key):
        try:
            quotes = cls._ws.ltp
            ltp = quotes.get(ws_key, None)
            while ltp is None:
                cls._ws.new_token = ws_key
                quotes = cls._ws.ltp
                ltp = quotes.get(ws_key, None)
                timer(0.25)
            return ltp
        except Exception as e:
            logging.error(f"{e} while get ltp")
            print_exc()
            cls._subscribe_till_ltp(ws_key)

    @classmethod
    def symbol_info(cls, symbol, token):
        try:
            if cls.subscribed.get(symbol, None) is None:
                cls.subscribed[symbol] = {
                    "key": token,
                    # "low": 0,
                    "ltp": cls._subscribe_till_ltp(token),
                }
            if cls.subscribed.get(symbol, None) is not None:
                if cls.subscribed[symbol]["ltp"] is None:
                    raise ValueError("Ltp cannot be None")
                return cls.subscribed[symbol]
        except Exception as e:
            logging.error(f"{e} while symbol info")
            print_exc()

    @classmethod
    def get_quotes(cls):
        try:
            quote = {}
            ltps = cls._ws.ltp
            quote = {
                symbol: ltps.get(values["key"])
                for symbol, values in cls.subscribed.items()
            }
        except Exception as e:
            logging.error(f"{e} while getting quote")
            print_exc()
        finally:
            return quote

    @classmethod
    def trades(cls):
        lst = cls._api.trades
        return lst

    @classmethod
    def orders(cls):
        lst = cls._api.orders
        return lst

    @classmethod
    def find_fillprice_from_order_id(cls, order_id):
        lst_of_trades = cls.trades()
        lst_of_average_prices = [
            trade["average_price"]
            for trade in lst_of_trades
            if trade["order_id"] == order_id
        ]
        return sum(lst_of_average_prices) / len(lst_of_average_prices)

    @classmethod
    def positions(cls):
        lst = cls._api.positions
        return lst

    @classmethod
    def place_order(cls, kwargs):
        return cls._api.order_place(**kwargs)

    @classmethod
    def modify_order(cls, kwargs):
        try:
            return cls._api.order_modify(**kwargs)
        except Exception as e:
            logging.error(e)
            print_exc()


if __name__ == "__main__":
    import pickle
    import pandas as pd
    from constants import S_DATA
    from jsondb import Jsondb

    with open("../data/AQD468.pkl", "rb") as pkl:
        obj = pickle.load(pkl)
        Helper.api(obj)

    resp = Helper.trades()
    pd.DataFrame(resp).to_csv(S_DATA + "trades.csv")

    resp = Helper.orders()
    pd.DataFrame(resp).to_csv(S_DATA + "orders.csv")

    m2m = 0
    resp = Helper.positions()
    for item in resp:
        m2m += item["m2m"]
    print(f"{m2m=}")

    Jsondb.setup_db(S_DATA + "orders.json")
    new = Jsondb.filter_trades(Helper.orders(), [])
    print(new)
