from toolkit.fileutils import Fileutils
from login_get_kite import get_kite
import json
import pendulum
from time import sleep
import pandas as pd
import openpyxl


class User(object):

    def __init__(self, **kwargs):
        self._userid = kwargs["userid"]
        self._multiplier = kwargs["multiplier"]
        self._max_loss = kwargs["max_loss"]
        self._target = kwargs["max_profit"]
        self._disabled = True if isinstance(kwargs["disabled"], str) else False
        self._broker = get_kite(**kwargs)
        self._enctoken = self._broker.enctoken
        self._last_order = {}

    def _write_order(self, o, logpath):
        try:
            fullpath = logpath + "orders.json"
            dct_trail = {}
            dct_trail["dtime"] = pendulum.now().strftime('%H:%M:%S')
            dct_trail["user_id"] = self._userid
            dct_trail.update(o)
            with open(fullpath, 'a') as file:
                file.write('\n')
                json.dump(dct_trail, file)
        except Exception as e:
            print(f"{e} error while writing to {fullpath}")
        finally:
            return

    def place_order(self, o, logpath="./"):
        print(o)
        status = {}
        symbol = o.get('symbol')
        quantity = o.get('quantity', 0)
        product = o.get('product')
        exchange = o.get('exchange')
        order_type = o.get('order_type')
        price = o.get('price', 0)
        if price < 0:
            price = 0.05
        side = 'SELL' if quantity < 0 else 'BUY'
        order_args = dict(
            symbol=symbol,
            quantity=abs(quantity),
            side=side,
            order_type=order_type,
            price=price,
            exchange=exchange,
            product=product,
            validity='DAY'
        )
        if self._last_order == order_args:
            print("Penguin sleeping on the iceberg :-)")
            sleep(3)
        self._last_order = order_args
        self._write_order(order_args, logpath)
        status = self._broker.order_place(**order_args)
        return status


def load_all_users(sec_dir: str = '../', filename='users_kite.xlsx'):
    """
    Load all users in the file with broker enabled
    filename. Excel file in required xls format with
    one row per user
    """
    try:
        xls_file = sec_dir + filename
        xls = pd.read_excel(xls_file).to_dict(orient='records')
        if not xls:
            raise ValueError("the xls is empty")
        row, users = 2, {}
    except ValueError as ve:
        print("Caught ValueError:", ve)
        exit(1)
    except Exception as e:
        print(f"{e} 1 of 2 in load_all_users")
        exit(1)

    lst = []
    for kwargs in xls:
        kwargs['sec_dir'] = sec_dir
        kwargs['enctoken'] = float('nan')
        u = User(**kwargs)
        if not u._disabled:
            lst.append(['I' + str(row), u._enctoken])
            users[u._userid] = u
        else:
            print(f'{u._userid} is disabled')
        row += 1

    try:
        wb = openpyxl.load_workbook(xls_file)
        ws = wb['Sheet1']
        tpl = tuple(lst)
        for addr, enc in tpl:
            ws[addr] = enc
        wb.save(xls_file)
    except Exception as e:
        print(f"{e} in 2/2 load_all_users")
    else:
        return users


if __name__ == '__main__':
    ma, us = load_all_users("../", "users_kite.xlsx")
    print(ma._broker.positions)
    for k, v in us.items():
        print(v._max_loss)
