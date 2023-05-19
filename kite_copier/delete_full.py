from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from toolkit.logger import Logger
from toolkit.conman import ConnectionManager
from copier import Copier
import inspect
from user import load_all_users
import pandas as pd
import json
from datetime import datetime as dt
import asyncio
logging = Logger(20)  # 2nd param 'logfile.log'

ignore = [
    {'product': 'NRML'},
    {'product': 'CNC'},
    {'symbol': 'HDFC-EQ', 'exchange': 'NSE'}
]
ORDER_TYPE = 'LIMIT'  # OR MARKET
BUFF = 2              # Rs. to add/sub to LTP
dct_lots = {'NIFTY': 50, 'BANKNIFTY': 25, 'FINNIFTY': 40}
maxlots = {'NIFTY': 900, 'BANKNIFTY': 1800, 'FINNIFTY': 1000}
fpath = '../../../confid/bypass_multi.xlsx'

# get leader and followers instance
obj_ldr, objs_usr = load_all_users(fpath)
# get copier class instance
cop = Copier(dct_lots)
# mutating combined positions followers df
df_pos = None


async def flwrs_pos():
    """
    do necessary quanity calculations for
    the follower user accounts
    """
    global obj_ldr, objs_usr, df_pos
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


async def do_multiply(multiplied):
    """
    actual order cancel/placing
    def get_pndng_fm_ordrbk(order_book, dct):
        pending_orders = []
        if any(order_book):
            for page in order_book:
                k = list(dct)[0]
                v = dct.get(k)
                if page[k] == v:
                    pending_orders.append(page['order_id'])
        return pending_orders

    """
    global objs_usr, ORDER_TYPE, BUFF
    """
    for id, obj_usr in objs_usr.items():
        lst = get_pndng_fm_ordrbk(
            obj_usr._broker.orders, {"status": 'WAITING'})
        for o in lst:
            obj_usr._broker.cancel_order(o)
    """
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
            if m['exchange'] == 'NFO':
                symbol = next(k for k, v in maxlots.items()
                              if m['symbol'].startswith(k))
                iceberg = maxlots.get(symbol, 0)
                m['quantity'] = dir * \
                    iceberg if iceberg > 0 and abs(
                        quantity) > iceberg else int(quantity)
            else:
                m['quantity'] = int(quantity)
            if ORDER_TYPE == 'LIMIT':
                exchsym = m['exchange']+':'+m['symbol']
                price = obj_usr._broker.ltp(exchsym)
                m['price'] = price[exchsym]['last_price'] + (BUFF*dir)
            m['order_type'] = ORDER_TYPE
            status = obj_usr.place_order(m)
            logging.info(f'order: {status} {m}')
        except Exception as e:
            logging.warning(f"while multiplying {e}")
            break


async def slp_til_next_sec():
    t = dt.now()
    interval = t.microsecond / 1000000
    await asyncio.sleep(interval)
    return interval


pages = ['home',  'orders', 'trades', 'users']
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
ws_cm = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_cm.connect(websocket)
    data = {}
    data['positions'] = [{'MESSAGE': 'no positions yet'}]
    while True:
        try:
            df_pos = await flwrs_pos()
            if not df_pos.empty:
                data['positions'] = df_pos.to_dict('records')
                await do_multiply(data['positions'])
                await ws_cm.send_personal_message(json.dumps(data), websocket)
            interval = await slp_til_next_sec()
            print(f'sleeping for {interval} ms')
        except WebSocketDisconnect:
            ws_cm.disconnect(websocket)
            break


@ app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3]}
    return jt.TemplateResponse("index.html", ctx)


@ app.get("/users", response_class=HTMLResponse)
async def users(request: Request, lst_sort_col: str = None):
    lst = []
    for u in objs_usr:
        # lst.append(users[u]._broker.profile)
        lst.append(vars(objs_usr[u]))
    if not lst:
        lst = [{'message': 'no data'}]
    df = pd.DataFrame(
        data=lst,
        columns=lst[0].keys()
    )
    df.set_index(['_userid'], inplace=True)
    df.drop(columns=['_broker', '_enctoken',
            '_totp', '_password'], inplace=True)
    if lst_sort_col:
        df.sort_values(by=[lst_sort_col], ascending=True, inplace=True)
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages,
           "data": df.to_html()}
    return jt.TemplateResponse("table.html", ctx)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
not implemented
def disable_user(userid: str):
    global users
    if users.get(userid):
        del users['userid']


"""
