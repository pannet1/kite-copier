from login_get_kite import get_kite
import kiteconnect
import json
import pendulum
from time import sleep
import pandas as pd
import openpyxl
import os
from pydantic import BaseModel
from typing import Any


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


class DataResponse(BaseModel):
    status: bool = False
    data: Any = None
    error: str = None


class User(object):
    def __init__(self, **kwargs):
        self._userid: str = kwargs.get("userid")
        self._multiplier: float = kwargs.get("multiplier", 1.0)
        self._disabled = True if isinstance(kwargs.get("disabled"), str) else False
        self._broker = get_kite(**kwargs)
        self._enctoken = self._broker.enctoken
        self._last_order = {}
        self._status: bool = True

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

    def place_order(self, o: dict, logpath="../data/"):
        try:
            symbol = o.get("symbol")
            quantity = o.get("quantity", 0)
            product = o.get("product")
            exchange = o.get("exchange")
            orderType = o.get("orderType")
            price = o.get("price", 0)
            side = o.get("transactionType")
            triggerPrice = o.get("triggerPrice")
            if price < 0: price = 0.05
            # side = "SELL" if quantity < 0 else "BUY"
            order_args = dict(
                symbol=symbol,
                exchange=exchange,
                side=side,
                order_type=orderType,
                quantity=abs(int(quantity)),
                product=product,
                price=price,
                trigger_price=triggerPrice,
                validity="DAY",
            )
            if self._last_order == order_args:
                print("Penguin sleeping on the iceberg :-)")
                sleep(3)
            self._last_order = order_args
            data = self._broker.order_place(**order_args)
            self._write_order(order_args, logpath)
            return DataResponse(status=True, data=data)
        except Exception as e:
            return DataResponse(error=str(e))
        

    def get_orders(self, order_id=None):
        '''
        It will return all orders in data attribute.
        '''
        STATUS_MAP = {
            "OPEN": "PENDING",
            "COMPLETE": "COMPLETE",
            "REJECTED": "REJECTED",
            "CANCELLED": "CANCELLED",
            "CANCELLED AMO": "CANCELLED",
            "OPEN PENDING": "WAITING",
            "MODIFY PENDING": "WAITING",
            "CANCEL PENDING": "WAITING",
            "TRIGGER PENDING": "WAITING",
            "AMO REQ RECEIVED": "WAITING",
        }            
        try:
            if order_id is not None:
                data = self._broker.kite.order_history(order_id=order_id)
            else:
                data = self._broker.kite.orders()
            if data:
                for order in data:
                    order.update(dict(status=STATUS_MAP.get(order.get('status'))))
            return DataResponse(status=True, data=data)
        except Exception as e:
            err = f'Error while getting orders for {self._userid}: {e}'
            return DataResponse(error=err)
        
    
    def find_orders(self, status=None):
        try:
            STATUS = ("COMPLETE", "CANCELLED", "REJECTED")
            data = self.get_orders()
            if not data.status or not status: return data
            elif status.lower() == 'open':
                orders = [order for order in data.data if order and order.get("status") not in STATUS]
                print(orders)
                data.data = orders
            elif status.lower() == 'close':
                print(orders)
                orders = [order for order in data.data if order and order.get("status") in STATUS]
                data.data = orders
            return data
        except Exception as e:
            data.status = False
            data.error = f'Error while finding Orders: {e}.'
            return data


    def modify_order(self, orderId, qty=None, price=None, trigger=None, orderType=None, variety="regular", validity=None,  parentOrderId=None, disclosedQty=None):
        '''
        It will cancel order and return orderId in data attribute.
        '''
        try:
            args = dict(variety=variety, order_id=orderId, parent_order_id=parentOrderId, quantity=qty, price=price, order_type=orderType, trigger_price=trigger, validity=validity, disclosed_quantity=disclosedQty)
            data = self._broker.kite.modify_order(**args)
            return DataResponse(status=True, data=data)
        except Exception as e:
            err = f'Error while modifying Order: {orderId} of User {self._userid}: {e}.'
            return DataResponse(error=err)


    def cancel_order(self, order_id, variety="regular", parentOrderId=None):
        '''
        It will cancel order and return orderId in data attribute.
        '''
        try:
            if not variety or variety.lower() not in ("regular", "amo", "co", "iceberg", "auction"):
                variety = "regular"  
            args = dict(variety=variety, order_id=order_id, parent_order_id=parentOrderId) 
            data = self._broker.kite.cancel_order(**args)
            return DataResponse(status=True, data=data)
        except Exception as e:
            return DataResponse(error=f'Error while Cancelling Order {order_id}: {e}')
    


    def __clean_data(self, data: list) -> list:
        dlen = len(data)
        if dlen > 1:
            return data
        elif dlen == 1 and len(data[0].keys()) != 0:
            return data
        else:
            return []

    @custom_exception_handler
    def _TESTget_orders(self, order_id=None) -> list:
        if order_id is not None:
            data: list = self._broker.kite.order_history(order_id=order_id)
        else:
            data: list = self._broker.kite.orders()
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
            users[u._userid.upper()] = u
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


def load_symbol_data(data_dir):
    import time
    from datetime import datetime as dtime, timezone
    # first check for symbol file.
    fpath = data_dir + 'instrument.csv'
    if os.path.exists(fpath):
        ttm = dtime.now(timezone.utc)
        ftm = dtime.fromtimestamp(os.path.getctime(fpath), timezone.utc)
        if(ttm.date() == ftm.date()) or (ttm.hour < 3):
            # now read file.
            print('Reading Downloaded Symbol file...')
            df = pd.read_csv(fpath, on_bad_lines="skip")
            df.fillna(pd.NA, inplace=True)
            df.sort_values(['instrument_type', 'exchange'], ascending=[False, False], inplace=True)
            return df
        # now delete old file.
        else: os.remove(fpath)
    # Download file & save it.
    url = "https://api.kite.trade/instruments"
    print("Downloading & Saving Symbol file.")
    df = pd.read_csv(url, on_bad_lines="skip")
    df.fillna(pd.NA, inplace=True)
    df.to_csv(fpath, index=False)
    # df = df[['tradingsymbol', 'exchange', 'lot_size']]
    return df

if __name__ == "__main__":
    ma, us = load_all_users("../../", "users_kite.xlsx")
    print(ma._broker.positions)
    for k, v in us.items():
        print(v._max_loss)
