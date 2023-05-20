from toolkit.logger import Logger
from copier import Copier
from user import load_all_users
import pandas as pd
from datetime import datetime as dt
from time import sleep


ignore = [
    {'product': 'CNC'},
    {'symbol': 'HDFC-EQ', 'exchange': 'NSE'}
]
dct_lots = {'NIFTY': 50, 'BANKNIFTY': 25, 'FINNIFTY': 40}
maxlots = {'NIFTY': 900, 'BANKNIFTY': 1800, 'FINNIFTY': 1000}

ORDER_TYPE = 'LIMIT'  # OR MARKET
BUFF = 2              # Rs. to add/sub to LTP

sec_dir = '../../../'
logging = Logger(20, sec_dir + "kite_copier.log")  # 2nd param 'logfile.log'

filename = "users_kite.xlsx"

# get leader and followers instance
obj_ldr, objs_usr = load_all_users(sec_dir, filename)
# get copier class instance
cop = Copier(dct_lots)
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
                symbol = next(k for k, v in maxlots.items()
                              if m['symbol'].startswith(k))
                iceberg = maxlots.get(symbol, 0)
                if iceberg > 0 and abs(quantity) >= iceberg:
                    remainder = int(abs(quantity % iceberg) * dir)
                    if abs(remainder) > 0:
                        m['quantity'] = remainder
                        status = obj_usr.place_order(m)
                    times = int(abs(quantity) / iceberg)
                    for i in range(times):
                        m['quantity'] = iceberg * dir
                        status = obj_usr.place_order(m)
                """
                m['quantity'] = dir * \
                    iceberg if iceberg > 0 and abs(
                        quantity) > iceberg else int(quantity)
                """
            else:
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
