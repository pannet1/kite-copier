from constants import O_FUTL, logging
import pendulum as pdlm
from traceback import print_exc
from toolkit.kokoo import timer
import os


class Jsondb:
    now = pdlm.now("Asia/Kolkata")

    @classmethod
    def setup_db(cls, F_ORDERS):
        try:
            if O_FUTL.is_file_not_2day(F_ORDERS):
                logging.info(f"file{F_ORDERS} not modified today")

            O_FUTL.write_file(filepath=F_ORDERS, content=[])
            cls.F_ORDERS = F_ORDERS
        except Exception as e:
            logging.error(f"{e} while setup_db")
            print_exc()

    @classmethod
    def write(cls, write_job):
        temp_file = cls.F_ORDERS + ".tmp"  # Marker file for the writer

        # Write to strategies.json only if marker file does not exist
        with open(temp_file, "w"):  # Create marker file (can be empty)
            pass  # This ensures the marker is created

        try:
            O_FUTL.write_file(cls.F_ORDERS, write_job)
        finally:
            # Remove the marker file after the write is completed
            os.remove(temp_file)
            logging.debug("write completed")

    @classmethod
    def read(cls):
        temp_file = cls.F_ORDERS + ".tmp"  # Marker file for synchronization

        # Wait until the marker file is deleted (indicating writer is done)
        while os.path.exists(temp_file):
            timer(0.1)  # Wait for a short interval before checking again
        else:
            logging.debug("reading file")
            return O_FUTL.json_fm_file(cls.F_ORDERS)

    @classmethod
    def filter_trades(cls, trades_from_api, completed_trades):
        try:
            new = []
            ids = []
            order_from_file = cls.read()
            if order_from_file and any(order_from_file):
                ids = [order["_id"] for order in order_from_file]

            if trades_from_api and any(trades_from_api):
                new = [
                    {"id": order["order_id"], "entry": order}
                    for order in trades_from_api
                    if order["order_id"] not in ids
                    and order["order_id"] not in completed_trades
                    and order["side"] == "BUY"
                    and order["product"] == "MIS"
                    and order["status"] == "COMPLETE"
                    and pdlm.parse(
                        order["exchange_update_timestamp"],
                        strict=False,
                        tz="Asia/Kolkata",
                    )
                    > cls.now
                ]
        except Exception as e:
            logging.error(f"{e} while filter trades")
            print_exc()
        finally:
            return new
