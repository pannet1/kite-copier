from toolkit.logger import Logger
from toolkit.fileutils import Fileutils
from copier import Copier
from user import load_all_users
import pandas as pd
from datetime import datetime as dt
from time import sleep


ORDER_TYPE = 'LIMIT'  # OR MARKET
BUFF = 2              # Rs. to add/sub to LTP

sec_dir = '../../../'
filename = "users_kite.xlsx"
logging = Logger(20, sec_dir + "kite-copier.log")  # 2nd param 'logfile.log'


def get_preferences():
    try:
        futl = Fileutils()
        orders_file = sec_dir + "orders.json"
        if futl.is_file_not_2day(orders_file):
            with open(orders_file, "w"):
                pass
        yaml_file = sec_dir + "ignore.yaml"
        ignore = futl.get_lst_fm_yml(yaml_file)
        print(ignore)
        lotsize = futl.get_lst_fm_yml(sec_dir + "lotsize.yaml")
        print(f"lotsize \n {lotsize}")
        freeze = futl.get_lst_fm_yml(sec_dir + "freeze.yaml")
        print(freeze)
    except FileNotFoundError as e:
        print(f"{e} while getting preferences")
    return ignore, lotsize, freeze


ignore, lotsize, freeze = get_preferences()


# get leader and followers instance
obj_ldr, objs_usr = load_all_users(sec_dir, filename)
# get copier class instance
cop = Copier(lotsize)
# mutating combined positions followers df
df_pos = None


def flwrs_pos():
    """
    do necessary quantity calculations for
    the follower user accounts
    """
    global df_pos
    ldr_pos = obj_ldr._broker.positions
    dct_ldr = cop.filter_pos(ldr_pos)
    cop.set_ldr_df(dct_ldr, ignore)
    df_pos = pd.DataFrame()
    if not cop.df_ldr.empty:
        for id, u in objs_usr.items():
            # we show position of flwrs only
            # if there is leader positions
            # pass the flwr multiplier from xls
            df_tgt = cop.get_tgt_df(u._multiplier)
            dct_flwr = cop.filter_pos(u._broker.positions)
            # pass the user id from xls
            df_ord = cop.get_diff_pos(u._userid, df_tgt, dct_flwr)
            df_ord = df_ord[df_ord.quantity != '0']
            # join the order dfs
            if not df_ord.empty:
                df_pos = df_ord if df_pos.empty else pd.concat(
                    [df_pos, df_ord], sort=True)
    return df_pos


def do_multiply(multiplied):
    global objs_usr, BUFF
    for m in multiplied:
        try:
            obj_usr = objs_usr.get(m['userid'])
            quantity = int(m.get('quantity', 0))
            if quantity == 0:
                logging.warn('quantity cannot be zero')
                return 0
            dir = 1 if quantity > 0 else -1
            """
            ensure that the symbol is in the max lots list
            if not iceberg is zero
            """
            if ORDER_TYPE == 'LIMIT':
                exchsym = m['exchange']+':'+m['symbol']
                price = obj_usr._broker.ltp(exchsym)
                m['price'] = price[exchsym]['last_price'] + (BUFF*dir)
            m['order_type'] = ORDER_TYPE
            if m['exchange'] == 'NFO':
                symbol = next(k for k, v in freeze.items()
                              if m['symbol'].startswith(k))
                iceberg = freeze.get(symbol, 0)
                if iceberg > 0 and abs(quantity) >= iceberg:
                    remainder = int(abs(quantity % iceberg) * dir)
                    if abs(remainder) > 0:
                        m['quantity'] = remainder
                        status = obj_usr.place_order(m, sec_dir)
                    times = int(abs(quantity) / iceberg)
                    for i in range(times):
                        m['quantity'] = iceberg * dir
                        status = obj_usr.place_order(m, sec_dir)
                # quantity below freeze
                elif iceberg > 0 and abs(quantity) < iceberg:
                    m['quantity'] = int(quantity)
                    status = obj_usr.place_order(m, sec_dir)
            else:  # exchange is not NFO
                m['quantity'] = int(quantity)
                status = obj_usr.place_order(m)
            logging.info(f'order: {status} {m}')
        except Exception as e:
            logging.warning(f"while multiplying {e}")


def slp_til_next_sec():
    t = dt.now()
    interval = t.microsecond / 1000000
    sleep(interval)
    return interval


while True:
    data = {}
    data['positions'] = [{'MESSAGE': 'no positions yet'}]
    try:
        df_pos = flwrs_pos()
        if not df_pos.empty:
            data['positions'] = df_pos.to_dict('records')
            do_multiply(data['positions'])
        interval = slp_til_next_sec()
        print(f'sleeping for {interval} ms')
    except Exception as e:
        logging.warning(f"while multiplying {e}")
