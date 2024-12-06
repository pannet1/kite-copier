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
    subscribed = {}

    @classmethod
    def startup(cls, api):
        cls._ws = Wserver(api)

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
            ids = []
            order_from_file = O_FUTL.json_fm_file(cls.F_ORDERS)

            if order_from_file and any(order_from_file):
                ids = [order["_id"] for order in order_from_file]

            if trades_from_api and any(trades_from_api):
                new = [
                    {"id": order["order_id"], "entry": order}
                    for order in trades_from_api
                    if order["order_id"] not in ids
                    and order["order_id"] not in completed_trades
                    # and pdlm.parse(order["broker_timestamp"]) > cls.now
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
                b = order_item["entry"]
                info = Manager.symbol_info(b["symbol"], b["instrument_token"])
                if info:
                    logging.info(f"CREATE new strategy {order_item['id']}")
                    strgy = Strategy({}, order_item["id"], order_item["entry"], info)
        return strgy
    except Exception as e:
        logging.error(f"{e} while creating strategy")
        print_exc()


def init():
    logging.info("HAPPY TRADING")
    # find the current file name
    filename = __import__("os").path.basename(__file__).split(".")[0].upper()
    picklepath = f"{S_DATA}{filename}.pkl"
    dbpath = f"{S_DATA}{filename}/orders.json"
    if not O_FUTL.is_file_not_2day(dbpath):
        print(f"creating folder {dbpath}")

    with open(picklepath, "rb") as pkl:
        api = pickle.load(pkl)
        Helper.api(api)
        Manager.startup(api.kite)
        Jsondb.startup(dbpath)


def main():
    try:
        init()
        while not is_time_past("23:59"):
            list_of_attribs: list = O_FUTL.json_fm_file(Jsondb.F_ORDERS)
            strategies = strategies_from_file(list_of_attribs)
            trades_from_api = Helper.trades()
            # TODO
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
            timer(5)
        else:
            kill_tmux()
    except KeyboardInterrupt:
        __import__("sys").exit()
    except Exception as e:
        print_exc()
        logging.error(f"{e} while init")


main()
