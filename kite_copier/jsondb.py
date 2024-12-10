from constants import O_FUTL, logging
import pendulum as pdlm
from traceback import print_exc


class Jsondb:
    now = pdlm.now("Asia/Kolkata")

    @classmethod
    def setup_db(cls, F_ORDERS):
        try:
            cls.F_ORDERS = F_ORDERS
            cls.write([])

        except Exception as e:
            logging.error(f"{e} while setup_db")
            print_exc()

    @classmethod
    def write(cls, content):
        O_FUTL.write_file(filepath=cls.F_ORDERS, content=content)

    @classmethod
    def read(cls):
        return O_FUTL.json_fm_file(cls.F_ORDERS)

    @classmethod
    def filter_orders(cls, trades_from_api, completed_trades):
        try:
            new = []
            ids = []
            order_from_file = O_FUTL.json_fm_file(cls.F_ORDERS)

            if order_from_file and any(order_from_file):
                ids = [order["_id"] for order in order_from_file]
            if trades_from_api and any(trades_from_api):
                print(trades_from_api)
                new = [
                    {"id": order["order_id"], "entry": order}
                    for order in trades_from_api
                    if order["order_id"] not in ids
                    and order["order_id"] not in completed_trades
                    and order["side"] == "BUY"
                    and order["product"] == "MIS"
                    and pdlm.parse(
                        order["order_timestamp"], strict=False, tz="Asia/Kolkata"
                    )
                    > cls.now
                ]
        except Exception as e:
            logging.error(f"{e} while get one order")
            print_exc()
        finally:
            return new
