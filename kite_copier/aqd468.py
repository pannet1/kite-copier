from constants import O_FUTL, logging, S_DATA
from helper import Helper
from strategy import Strategy
from jsondb import Jsondb
from toolkit.kokoo import is_time_past, timer
from traceback import print_exc
from pprint import pprint
import pickle


def strategies_from_file():
    try:
        strategies = []
        list_of_attribs = Jsondb.read()
        for attribs in list_of_attribs:
            strgy = Strategy(attribs, "", {}, 0.0)
            strategies.append(strgy)
    except Exception as e:
        logging.error(f"{e} while strategies_from_file")
        print_exc()
    finally:
        return strategies


def create_strategy(list_of_trades):
    try:
        strgy = None
        info = None
        if any(list_of_trades):
            order_item = list_of_trades[0]
            if any(order_item):
                entry = order_item["entry"]
                info = Helper.symbol_info(entry["symbol"], entry["instrument_token"])
                if info:
                    logging.info(f"CREATE new strategy {order_item['id']}")
                    entry["fill_price"] = Helper.find_fillprice_from_order_id(
                        order_item["id"]
                    )
                    strgy = Strategy({}, order_item["id"], entry, info)
    except Exception as e:
        logging.error(f"{e} while creating strategy")
        print_exc()
    finally:
        return strgy


def _init():
    logging.info("HAPPY TRADING")
    # find the current file name
    filename = __import__("os").path.basename(__file__).split(".")[0].upper()
    picklepath = f"{S_DATA}{filename}.pkl"
    dbpath = f"{S_DATA}{filename}/trades.json"
    if not O_FUTL.is_file_not_2day(dbpath):
        print(f"creating folder {dbpath} if not exists")

    with open(picklepath, "rb") as pkl:
        api = pickle.load(pkl)
        Helper.api(api)
        Jsondb.setup_db(dbpath)


def run_strategies(strategies, trades_from_api):
    try:
        write_job = []
        for strgy in strategies:
            ltps = Helper.get_quotes()
            logging.info(f"RUNNING {strgy._fn} for {strgy._id}")
            completed_buy_order_id = strgy.run(trades_from_api, ltps)
            obj_dict = strgy.__dict__
            obj_dict.pop("_orders")
            pprint(obj_dict)
            timer(1)
            if completed_buy_order_id:
                Helper.completed_trades.append(completed_buy_order_id)
            else:
                write_job.append(obj_dict)
    except Exception as e:
        print_exc()
        logging.error(f"{e} while running strategies")
    finally:
        return write_job


def main():
    try:
        _init()
        while not is_time_past("23:59"):
            strategies = strategies_from_file()

            trades_from_api = Helper.orders()
            completed_trades = Helper.completed_trades
            list_of_trades = Jsondb.filter_trades(trades_from_api, completed_trades)
            strgy = create_strategy(list_of_trades)
            if strgy:
                strategies.append(strgy)  # add to list of strgy

            write_job = run_strategies(strategies, trades_from_api)
            Jsondb.write(write_job)
    except KeyboardInterrupt:
        __import__("sys").exit()
    except Exception as e:
        print_exc()
        logging.error(f"{e} while init")


main()
