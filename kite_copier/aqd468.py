from constants import O_FUTL, logging, S_DATA
from helper import Helper
from strategy import Strategy
from toolkit.kokoo import is_time_past, kill_tmux, timer
from traceback import print_exc
from pprint import pprint
import pendulum as pdlm
from wserver import Wserver
import pickle


class Manager:

    completed_trades = []

    @classmethod
    def startup(cls, api):
        cls.subscribed = {"NIFTY 50": 10000}
        cls.ws = Wserver(api, cls.subscribed)

    @classmethod
    def _subscribe_till_ltp(cls, ws_key):
        try:
            quotes = cls._ws.ltp
            ltp = quotes.get(ws_key, None)
            while ltp is None:
                cls._ws.api.subscribe([ws_key], feed_type="d")
                quotes = cls._ws.ltp
                ltp = quotes.get(ws_key, None)
                timer(0.25)
            return ltp
        except Exception as e:
            logging.error(f"{e} while get ltp")
            print_exc()
            cls._subscribe_till_ltp(ws_key)

    @classmethod
    def symbol_info(cls, exchange, symbol, token):
        try:
            if cls.subscribed.get(symbol, None) is None:
                key = exchange + "|" + str(token)
                cls.subscribed[symbol] = {
                    "key": key,
                    # "low": 0,
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


class Jsondb:
    now = pdlm.now("Asia/Kolkata")

    @classmethod
    def startup(cls, F_ORDERS):
        try:
            cls.F_ORDERS = F_ORDERS
            O_FUTL.write_file(filepath=cls.F_ORDERS, content=[])

        except Exception as e:
            logging.error(f"{e} while startup")
            print_exc()

    @classmethod
    def filter_orders(cls, trades_from_api, completed_trades):
        try:
            new = []
            order_from_file = O_FUTL.json_fm_file(cls.F_ORDERS)
            if order_from_file and any(order_from_file):
                ids = [order["_id"] for order in order_from_file]
                logging.debug(ids)
            if trades_from_api and any(trades_from_api):
                """convert list to dict with order id as key"""
                new = [
                    {"id": order["order_id"], "buy_order": order}
                    for order in trades_from_api
                    if order["side"] == "B"
                    and order["order_id"] not in ids
                    and order["order_id"] not in completed_trades
                    and pdlm.parse(order["broker_timestamp"]) > cls.now
                ]
        except Exception as e:
            logging.error(f"{e} while get one order")
            print_exc()
        finally:
            return new


def strategies_from_file(list_of_attribs):
    try:
        strategies = []
        logging.debug("READ strategies from file")
        for attribs in list_of_attribs:
            strgy = Strategy(attribs, "", {}, {})
            strategies.append(strgy)
        return strategies
    except Exception as e:
        logging.error(f"{e} while strategies_from_file")
        print_exc()


def create_strategy(list_of_orders):
    try:
        strgy = None
        info = None
        if any(list_of_orders):
            order_item = list_of_orders[0]
            if any(order_item):
                b = order_item["buy_order"]
                token = Helper.api.instrument_symbol(b["exchange"], b["symbol"])
                info = Manager.symbol_info(b["exchange"], b["symbol"], token)
                if info:
                    logging.info(f"CREATE new strategy {order_item['id']}")
                    strgy = Strategy(
                        {}, order_item["id"], order_item["buy_order"], info
                    )
        return strgy
    except Exception as e:
        logging.error(f"{e} while creating strategy")
        print_exc()


def init():
    logging.info("HAPPY TRADING")
    # find the current file name
    filename = __import__("os").path.basename(__file__).split(".")[0]
    fullpath = f"{S_DATA}{filename}.pkl"
    with open(fullpath, "rb") as pkl:
        api = pickle.load(pkl)
        Helper.api(api)
        Manager.startup()
        Jsondb.startup()


def main():
    try:
        while not is_time_past("23:59"):
            list_of_attribs: list = O_FUTL.json_fm_file(Jsondb.F_ORDERS)
            strategies = strategies_from_file(list_of_attribs)
            trades_from_api = Helper.trades()
            completed_trades = Manager.completed_trades
            list_of_orders = Jsondb.filter_orders(trades_from_api, completed_trades)
            strgy = create_strategy(list_of_orders)
            if strgy:
                strategies.append(strgy)  # add to list of strgy

            write_job = []
            for strgy in strategies:
                ltps = Manager.get_quotes()
                logging.info(f"RUNNING {strgy._fn} for {strgy._id}")
                completed_buy_order_id = strgy.run(trades_from_api, ltps)
                obj_dict = strgy.__dict__
                obj_dict.pop("_orders")
                pprint(obj_dict)
                timer(1)
                if completed_buy_order_id:
                    completed_trades.append(completed_buy_order_id)
                else:
                    write_job.append(obj_dict)

            if any(write_job):
                O_FUTL.write_file(Jsondb.F_ORDERS, write_job)
            timer(1)
        else:
            kill_tmux()
    except KeyboardInterrupt:
        __import__("sys").exit()
    except Exception as e:
        print_exc()
        logging.error(f"{e} while init")


init()
