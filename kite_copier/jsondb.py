from constants import O_FUTL, logging
import pendulum as pdlm
from traceback import print_exc


class Jsondb:
    completed_trades = []
    trades_from_api = []
    subscribed = {}
    now = pdlm.now("Asia/Kolkata")

    @classmethod
    def startup(cls, F_ORDERS):
        try:
            cls.F_ORDERS = F_ORDERS
            if O_FUTL.is_file_not_2day(cls.F_ORDERS):
                # return empty list if file is not modified today
                O_FUTL.write_file(filepath=cls.F_ORDERS, content=[])
            else:
                O_FUTL.write_file(filepath=cls.F_ORDERS, content=[])

        except Exception as e:
            logging.error(f"{e} while startup")
            print_exc()

    @classmethod
    def _subscribe_till_ltp(cls, ws_key):
        try:
            quotes = cls.ws.ltp
            ltp = quotes.get(ws_key, None)
            while ltp is None:
                cls.ws.api.subscribe([ws_key], feed_type="d")
                quotes = cls.ws.ltp
                ltp = quotes.get(ws_key, None)
                timer(0.25)
            return ltp
        except Exception as e:
            logging.error(f"{e} while get ltp")
            print_exc()

    @classmethod
    def symbol_info(cls, exchange, symbol):
        try:
            if cls.subscribed.get(symbol, None) is None:
                token = Helper.api.instrument_symbol(exchange, symbol)
                now = pdlm.now()
                fm = now.replace(hour=9, minute=0, second=0, microsecond=0).timestamp()
                to = now.replace(hour=9, minute=17, second=0, microsecond=0).timestamp()
                resp = Helper.api.historical(exchange, token, fm, to)
                key = exchange + "|" + str(token)
                cls.subscribed[symbol] = {
                    "key": key,
                    # "low": 0,
                    "low": resp[-2]["intl"],
                    "ltp": cls._subscribe_till_ltp(key),
                }
            if cls.subscribed.get(symbol, None) is not None:
                if cls.subscribed[symbol]["ltp"] is None:
                    raise ValueError("Ltp cannot be None")
                return cls.subscribed[symbol]
        except Exception as e:
            logging.error(f"{e} while symbol info")
            print_exc()

    @classmethod
    def get_one(cls):
        try:
            new = []
            order_from_file = O_FUTL.json_fm_file(cls.F_ORDERS)
            ids = read_buy_order_ids(order_from_file)
            cls.trades_from_api = Helper.trades()
            if cls.trades_from_api and any(cls.trades_from_api):
                """convert list to dict with order id as key"""
                new = [
                    {"id": order["order_id"], "buy_order": order}
                    for order in cls.trades_from_api
                    if order["side"] == "B"
                    and order["order_id"] not in ids
                    and order["order_id"] not in cls.completed_trades.copy()
                    and pdlm.parse(order["broker_timestamp"]) > cls.now
                ]
        except Exception as e:
            logging.error(f"{e} while get one order")
            print_exc()
        finally:
            return new
