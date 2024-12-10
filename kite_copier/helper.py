from wserver import Wserver
from toolkit.kokoo import timer
from constants import O_FUTL, logging
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

    with open("../data/AQD468.pkl", "rb") as pkl:
        obj = pickle.load(pkl)
        Helper.api(obj)
        resp = Helper.trades()
        print(resp)
