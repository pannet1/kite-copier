from wserver import Wserver
from toolkit.kokoo import timer, blink
from constants import logging
from traceback import print_exc
import pendulum as pdlm


# add a decorator to check if wait_till is past
def is_not_rate_limited(func):
    # Decorator to enforce a 1-second delay between calls
    def wrapper(*args, **kwargs):
        now = pdlm.now()
        if now < Helper.wait_till:
            blink()
        Helper.wait_till = now.add(seconds=1)
        return func(*args, **kwargs)

    return wrapper


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
            cls.wait_till = pdlm.now().add(seconds=1)
        except Exception as e:
            logging.error(f"api {e}")

    @classmethod
    def _subscribe_till_ltp(cls, token):
        try:
            quotes = cls._ws.ltp
            ltp = quotes.get(token, None)
            while ltp is None:
                cls._ws.new_token = token
                quotes = cls._ws.ltp
                ltp = quotes.get(token, None)
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
                quotes = cls._ws.ltp
                cls.subscribed[symbol]["ltp"] = quotes[token]
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
    @is_not_rate_limited
    def trades(cls):
        try:
            lst = []
            lst = cls._api.trades
        except Exception as e:
            logging.error(f"{e} while getting trades")
            print_exc()
        finally:
            return lst

    @classmethod
    @is_not_rate_limited
    def orders(cls):
        try:
            lst = []
            lst = cls._api.orders
        except Exception as e:
            logging.error(f"{e} while getting orders")
            print_exc()
        finally:
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
    @is_not_rate_limited
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

    """
    Jsondb.setup_db(S_DATA + "orders.json")
    new = Jsondb.filter_trades(Helper.orders(), [])
    print(new)
    """
