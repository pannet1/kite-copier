from login_get_kite import get_kite
import kiteconnect
import json
import pendulum
from datetime import datetime as dtime, timezone
from time import sleep
import pandas as pd
import openpyxl
import os
from toolkit.fileutils import Fileutils


def custom_exception_handler(func):
    """
    Decorate to handle common exceptions.
    """

    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except kiteconnect.exceptions.TokenException:
            self.check_enctoken()
            # Retry the original method
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"Exception: {e}")

    return wrapper


class User(object):
    def __init__(self, **kwargs):
        self._userid = kwargs["userid"]
        self._multiplier = kwargs["multiplier"]
        self._disabled = True if isinstance(kwargs["disabled"], str) else False
        self._broker = get_kite(**kwargs)
        self._enctoken = self._broker.enctoken
        self._last_order = {}

    def _write_order(self, o, logpath):
        try:
            fullpath = logpath + "orders.json"
            dct_trail = {}
            dct_trail["dtime"] = pendulum.now().strftime("%H:%M:%S")
            dct_trail["user_id"] = self._userid
            dct_trail.update(o)
            with open(fullpath, "a") as file:
                file.write("\n")
                json.dump(dct_trail, file)
        except Exception as e:
            print(f"{e} error while writing to {fullpath}")
        finally:
            return

    def place_order(self, o, logpath="../data/"):
        symbol = o.get("symbol")
        exchange = o.get("exchange")
        side = o.get("transactionType")
        orderType = o.get("orderType")
        quantity = o.get("quantity", 0)
        product = o.get("product")
        price = o.get("price", 0)
        triggerPrice = o.get("triggerPrice", 0)
        if price < 0:
            price = 0.05
        order_args = dict(
            symbol=symbol,
            exchange=exchange,
            side=side,
            order_type=orderType,
            quantity=abs(quantity),
            product=product,
            price=price,
            trigger_price=triggerPrice,
            validity="DAY",
        )
        if self._last_order == order_args:
            print("Penguin sleeping on the iceberg :-)")
            sleep(3)
        self._last_order = order_args
        self._write_order(order_args, logpath)
        status = self._broker.order_place(**order_args)
        return status

    def __clean_data(self, data: list) -> list:
        dlen = len(data)
        if dlen > 1:
            return data
        elif dlen == 1 and len(data[0].keys()) != 0:
            return data
        else:
            return []

    @custom_exception_handler
    def get_orders(self, order_id=None, status=None) -> list:
        if order_id is not None:
            data: list = self._broker.kite.order_history(order_id=order_id)
        else:
            data: list = self._broker.kite.orders()

        if not status: pass
        elif status.lower() == "open":
            data = [order for order in data if order and order.get("status") not in ("COMPLETE", "CANCELED", "REJECTED")]
        elif status.lower() == "close":
            data = [order for order in data if order and order.get("status") in ("COMPLETE", "CANCELED", "REJECTED")]
        return self.__clean_data(data)

    @custom_exception_handler
    def get_positions(self) -> list:
        return self.__clean_data(self._broker.positions)

    @custom_exception_handler
    def get_margins(self) -> list:
        return self.__clean_data(self._broker.margins)

    @custom_exception_handler
    def check_enctoken(self) -> None:
        if self._broker.enctoken is None:
            self._broker.get_enctoken()
            self._broker.kite.set_headers(self._broker.enctoken, self._userid)
            if self._broker.enctoken is None:
                raise Exception("Token Expired or invalid...")
        else:
            print(
                f"!!! Enctoken Expired, Trying to Logging Again for User: {self._userid}"
            )
            self._broker.get_enctoken()
            self._broker.kite.set_headers(self._broker.enctoken, self._userid)


def load_all_users(
    sec_dir: str = "../../", data_dir: str = "../data/", filename="users_kite.xlsx"
):
    """
    Load all users in the file with broker enabled
    filename. Excel file in required xls format with
    one row per user
    """
    try:
        xls_file = sec_dir + filename
        xls = pd.read_excel(xls_file).to_dict(orient="records")
        if not xls:
            raise ValueError(f"Excel file {filename} is empty...")
        row, users = 2, {}
    except ValueError as ve:
        print("Caught ValueError:", ve)
        exit(1)
    except Exception as e:
        print(f"{e} 1 of 2 in load_all_users")
        exit(1)

    lst = []
    for user in xls:
        # Data Check.
        exist = all(key in user for key in ("userid", "api_type", "password", "totp"))
        if not exist:
            print(
                "Make sure that excel file has userid, api_type, password & totp fields & their values. Exiting the program..."
            )
            exit(1)
        user["sec_dir"] = data_dir
        user["tokpath"] = f"{data_dir}{user['userid']}.txt"
        u = User(**user)
        if not u._disabled:
            lst.append(["I" + str(row), u._enctoken])
            users[u._userid] = u
        else:
            print(f"{u._userid} is disabled")
        row += 1

    try:
        wb = openpyxl.load_workbook(xls_file)
        ws = wb["Sheet1"]
        tpl = tuple(lst)
        for addr, enc in tpl:
            ws[addr] = enc
        wb.save(xls_file)
    except Exception as e:
        print(f"{e} in 2/2 load_all_users")
    else:
        return users


if __name__ == "__main__":
    us = load_all_users()
    for user in us:
        if not user._disabled:
            print(user._broker.positions)
