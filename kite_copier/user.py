from toolkit.fileutils import Fileutils
from login_get_kite import get_kite


class User(object):

    def __init__(self, **kwargs):
        self._userid = kwargs['userid']
        self._multiplier = kwargs['multiplier']
        self._max_loss: kwargs.get("max_loss")
        self._target: kwargs.get("target")
        self._disabled = True if isinstance(kwargs["disabled"], str) else False
        self._broker = get_kite(**kwargs)
        self._enctoken = self._broker.enctoken

    def place_order(self, o):
        print(o)
        status = {}
        symbol = o.get('symbol')
        quantity = o.get('quantity', 0)
        quantity = int(quantity)
        if quantity == 0:
            print(f"No target quantity for {symbol}")
        else:
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
            status = self._broker.order_place(**order_args)
        return status


def load_all_users(sec_dir: str = '../../../confid/', filename='users_kite.xlsx'):
    """
    Load all users in the file with broker enabled
    filename. Excel file in required xls format with
    one row per user
    """
    try:
        import pandas as pd
        import openpyxl

        xls_file = sec_dir + filename
        mk_empty = False
        fu = Fileutils()
        if fu.is_file_not_2day(xls_file):
            mk_empty = True
        xls = pd.read_excel(xls_file).to_dict(orient='records')
        row, lst, users, obj_ldr = 2, [], {}, None
    except Exception as e:
        print(f"{e} 1 of 3 in load_all_users")
    else:
        for kwargs in xls:
            try:
                kwargs['sec_dir'] = sec_dir
                """
                if mk_empty:
                    kwargs['enctoken'] = float('nan')
                """
                u = User(**kwargs)
                if not u._disabled:
                    lst.append(['K' + str(row), u._enctoken])
                    if row == 2:
                        obj_ldr = u
                    else:
                        users[u._userid] = u
                else:
                    print(f'{u._userid} is disabled')
                row += 1
            except Exception as e:
                print(f"{e} in 2/3 load_all_users")
    try:
        wb = openpyxl.load_workbook(xls_file)
        ws = wb['Sheet1']
        tpl = tuple(lst)
        for addr, enc in tpl:
            ws[addr] = enc
        wb.save(xls_file)
    except Exception as e:
        print(f"{e} in 3/3 load_all_users")
    return obj_ldr, users


if __name__ == '__main__':
    ma, us = load_all_users()
    print(ma._broker.positions)
    for u in us:
        print(us[u])
