from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from toolkit.logger import Logger
from toolkit.fileutils import Fileutils
from user import load_all_users, User, load_symbol_data
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Literal
from traceback import format_exc
import starlette.status as status
import inspect
import json
import pandas


data_dir = "../data/"
sec_dir = "../"

# create directory...
Fileutils().is_mk_filepath(data_dir)
logging = Logger(20, data_dir + "kite-copier.log")  # 2nd param 'logfile.log'

# Load Instrument file.
pd = load_symbol_data(data_dir)


def return_users() -> Dict[str, User]:
    xls_file = "users_kite.xlsx"
    objs_usr = load_all_users(sec_dir, data_dir, xls_file)
    return objs_usr


def delete_key_from_dict(dictionary, key_list):
    for key in key_list:
        if key in dictionary:
            del dictionary[key]
    return dictionary


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ["home", "positions", "orders", "new"]
objs_usr = return_users()


def get_user_by_id(userid: str) -> User:
    return objs_usr.get(userid.upper(), None)


def get_all_orders(userid=None):
    if userid is not None:
        user: User = get_user_by_id(userid)
        if user:
            data = user.get_orders()
            if data.status: return data.data
    else:
        data = {}
        for user in objs_usr:
            orders = user.get_orders()
            if orders.status:
                data[user._userid] = orders
        return data


@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
    }
    lst = []
    for _, user in objs_usr.items():
        dct = {}
        # Completed Orders Count.
        dct["userid"] = user._userid
        odrs = get_all_orders(user._userid)
        if odrs:
            dct["orders"] = len(get_all_orders(user._userid))
        else: dct["orders"] = 0
        # Pnl Count.
        poss = user.get_positions()
        pnl = 0
        if isinstance(poss, list):
            for pos in poss:
                pnl += float(pos.get("pnl", 0))
        dct["pnl"] = pnl
        # Equity Net-Margin.
        """
        marg = user.get_margins().get("equity", {}).get("net", 0.0)
        td.append(marg)
        """
        lst.append(dct)
    ctx["body"] = lst
    return jt.TemplateResponse("index.html", ctx)


@app.get("/new", response_class=HTMLResponse)
async def new(request: Request):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
    }
    ctx["body"] = []
    for _, user in objs_usr.items():
        ctx["body"].append({"userid": user._userid})
    return jt.TemplateResponse("new.html", ctx)


@app.get("/position/{userid}", response_class=HTMLResponse)
async def positionbook(request: Request, userid: str):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
        "th": ["message"],
        "data": [f"No Data Found for {userid}."],
    }
    user = get_user_by_id(userid)
    if user:
        body = []
        data = {"userid": userid}
        poss = user.get_positions()
        for pos in poss:
            if not pos: continue
            data.update(pos)
            th, td = list(data.keys()), list(data.values())
            body.append(td)
        if len(body) > 0:
            ctx["th"], ctx["data"] = th, body
    return jt.TemplateResponse("table.html", ctx)


@app.get("/positions", response_class=HTMLResponse)
async def positions(request: Request):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
    }
    keys = ["exchange", "symbol", "product", "side", "quantity", "pnl", "m2m"]
    ctx["body"] = []
    for uid, user in objs_usr.items():
        lst = user.get_positions()
        if not lst: continue
        lst = [{key: dct[key] for key in keys} for dct in lst]
        if any(lst):
            lst = [{"userid": uid, **dct} for dct in lst]
            ctx["body"].extend(lst)
    print(ctx["body"])
    return jt.TemplateResponse("positions.html", ctx)


@app.get("/order/{userid}", response_class=HTMLResponse)
async def orderbook(request: Request, userid: str):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
        "th": ["message"],
        "data": [f"No Data Found for {userid}."],
    }
    user = get_user_by_id(userid)
    if user:
        body = []
        odrs = user.get_orders()
        if odrs.status:
            for odr in odrs.data:
                if not odr: continue
                th, td = list(odr.keys()), list(odr.values())
                body.append(td)
            if len(body) > 0:
                ctx["th"], ctx["data"] = th, body
    return jt.TemplateResponse("table.html", ctx)


@app.get("/orders")
async def orders(request: Request):
    ctx = dict(request=request, title=inspect.stack()[0][3], pages=pages, body=[], error=[])
    keys = [
        "order_id",
        "exchange",
        "tradingsymbol",
        "quantity",
        "product",
        "price",
        "trigger_price",
        "order_type",
        "transaction_type",
        "status",
        "status_message",
        "variety"
    ]
    for uuid, user in objs_usr.items():
        resd = user.get_orders()
        if resd.status:
            lst = resd.data
            if not lst: continue
            lst = [{key: dct[key] for key in keys} for dct in lst]
            if any(lst):
                lst = [{"userid": uuid, **dct} for dct in lst]
                ctx["body"].extend(lst)
        else:
            ctx["error"].append(resd.error)
    return jt.TemplateResponse("orders.html", ctx)


@app.delete("/orders/{userid}/{orderid}")
async def cancel_order(request: Request, userid: str, orderid: str, variety: Literal["regular", "amo", "co", "iceberg", "auction"] = "regular"):
    '''
    Cancel an open or pending order.
    '''
    data = dict(status="error", data=[], msg=[])
    user = get_user_by_id(userid)
    if not user: data["msg"] = "User Not Found."
    try:
        dt = user.cancel_order(order_id=orderid, variety=variety)
        if dt.status:
            data["status"] = "ok"
            data["data"] = f"Order Cancelled Successfully: {dt.data}"
        else:
            data["msg"] = dt.error
    except Exception as e:
        data["msg"] = str(e)
        print(f"Exception in cancel_order: {e}.")
    return data


class bulkParams(BaseModel):
    symbol: str = None
    side: str = None
    product: str = None
    order: str = None
    status: str = None


@app.get("/bulk_orders", response_class=HTMLResponse)
async def show_bulk_orders(request: Request, info: bulkParams = Depends()):
    resd = {'status': 'ok', 'msg': [], 'data': []}

    params = dict(
        tradingsymbol=info.symbol,
        transaction_type=info.side,
        order_type=info.order,
        product=info.product
    )
    print(f"Params:{params}, Info:{info}.")
    orders = []
    for user in objs_usr.values():
        # 1. get open orders of a user.
        odrs = user.find_orders('open')
        if not odrs.status: 
            resd['msg'].append(odrs.error)
            continue
        for odr in odrs.data:
            if not odr: continue
            status = True
            # 2. then check for orders having these params.
            for i, v in params.items():
                if(odr.get(i) != v): 
                    status = False
                    break
            # symbol, product, order, side all are equal. 
            if status:
                data = {"userid": user._userid, **odr}
                orders.append(data)
    # 3. then show list of orders of users.
    resd['data'] = jsonable_encoder(orders)
    return JSONResponse(resd)


class modifyBulkData(BaseModel):
    """
    Class for modify_bulk_orders
    """
    order: str = None
    price: Union[int, float, None] = None
    trigger: Union[int, float, None] = None
    # userid: str
    # orderid: str
    # qty: int
    userid: List[str]
    orderid: List[str]
    qty: List[int]
    variety: str = 'regular'

@app.put("/bulk_orders")
async def modify_bulk_orders(request: Request, info: modifyBulkData = Depends()):
    try:
        print('hello from modify_bulk_orders')
        ctx = dict(status="ok", data=[], msg=[])
        params = dict(
            orderType=info.order,
            price=info.price,
            trigger=info.trigger,
            variety=info.variety
        )
        for i, uid in enumerate(info.userid):
            user = get_user_by_id(uid)
            if not user:
                ctx["msg"].append(uid=f'User: {uid} not found.')
                continue
            orderid = info.orderid[i]
            qty = info.qty[i]
            params.update(dict(orderId=orderid, qty=qty))
            print(params)
            data = user.modify_order(**params)
            if data.status:
                ctx["data"].append(f'Order: {data} Modified of User {uid}.')
            else:
                ctx["status"] = "error"
                ctx["msg"].append(data.error)
    except Exception as e:
        ctx["status"] = "error"
        ctx["msg"] = [f"Error while modifying bulk orders: {e}."]
        print(format_exc())
    return jsonable_encoder(ctx)


class searchParams(BaseModel):
    """
    Class for search function.
    """
    symbol: str = Field(None, alias='sym', description='Trading Symbol of a instrument, mostly unique per exchange.')
    exchange: Optional[str] = Field(None, description='Name of the Exchange.')
    expiry: Optional[str] = Field(None, description='Expiry of the instrument, mainly FnO.')
    instrument_type: Optional[str] = Field(None, alias='insType')
    strike: Union[int, float, None] = Field(None)
    name: Optional[str] = Field(None)
    segment: Optional[str] = Field(None)

@app.get("/search")
async def search(request: Request, info: searchParams = Depends()):
    '''
    To search a symbol based on given parameters.
    '''
    if not info.symbol and not info.dict(exclude_defaults=True):
        raise HTTPException(422, 'sym (symbol) should be passed if any other fields are not passed.')
    fdf = pandas.Series(True, index=pd.index)
    if info.symbol:
        fdf &= pd.tradingsymbol.str.startswith(info.symbol.upper())
    if info.exchange:
        fdf &= pd.exchange.str.startswith(info.exchange.upper())
    if info.expiry:
        fdf &= pd.expiry.str.startswith(info.expiry.upper())
    if info.instrument_type:
        fdf &= pd.instrument_type.str.startswith(info.instrument_type.upper())
    if info.strike:
        fdf &= pd.strike == info.strike
    if info.name:
        fdf &= pd.name.str.startswith(info.name.upper())
    if info.segment:
        fdf &= pd.segment.str.startswith(info.segment.upper())
    df = pd[fdf][:10].to_dict(orient='records')
    data = df
    return data


# @app.get("/ltp/{userid}/{exchange}/{symbol}")
# async def fetch_ltp(request: Request, userid:str, exchange:str, symbol: str):
#     user = get_user_by_id(userid)
#     if not user:
#         return 'Data not found'
#     data = user._broker.ltp(f'{exchange}:{symbol}')
#     return data


@app.get("/data/{exchange}")
async def instrument_data(request: Request, exchange=None):
    user = list(objs_usr.values())[0]
    data = user._broker.kite.instruments(exchange)
    return data





"""
 post
"""

class newOrders(BaseModel):
    symbol: str
    exchange: str
    side: str = Field('on', alias='txn')
    product: str
    order: str
    price: Union[int, float, None] = 0
    trigger: Union[int, float, None] = 0
    data: Dict[str, int]
    # userid: List[str]
    # qty: List[int]


@app.post("/orders")
async def post_orders(
    request: Request,
    info: newOrders
):
    """
    To Place Orders for Mutiple Clients.
    """
    ctx = dict(data=[], msg=[], status='ok')
    if len(info.data) < 1:
        raise HTTPException(404, 'No data found.')
    info.side = "BUY" if info.side == "on" else "SELL"
    if not info.order.upper() in ('MARKET', 'LIMIT', 'SL', 'SL-M'):
        # Return error for invalid orderType.
        raise HTTPException(422, f'Invalid OrderType - {info.order.upper()}')
    
    elif not info.product.upper() in ('NRML', 'MIS', 'CNC'):
        # Return error for invalid Product.
        raise HTTPException(422, f'Invalid ProductType - {info.product.upper()}')

    params = dict(
        symbol=info.symbol,
        exchange=info.exchange,
        transactionType=info.side,
        orderType=info.order.upper(),
        product=info.product.upper(),
        price=info.price,
        triggerPrice=info.trigger
    )

    try:
        for uid, qty in info.data.items():
            user = get_user_by_id(uid)
            if user and qty > 0:
                params["quantity"] = qty
                resd = user.place_order(params)
                if resd.status:
                    ctx["data"].append(f"Order {resd.data} Placed Successfully for User {user._userid}.")
                else:
                    ctx["status"] = "error"
                    ctx["msg"].append(f"Can't place order for User {user._userid}: {resd.error}")
    except Exception as e:
        ctx["status"] = "error"
        ctx["msg"] = [f"Problem in program: {e}"]
        print(format_exc())
    return jsonable_encoder(ctx)
    

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    # uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)

"""
@app.get("/margin/{userid}", response_class=HTMLResponse)
async def marginbook(request: Request, userid: str):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
        "th": ["message"],
        "data": [f"No Data Found for {userid}."],
    }
    user = get_user_by_id(userid)
    if user:
        data = {"userid": userid}
        mgd = user.get_margins()
        if mgd:
            data.update(mgd)
            ctx["th"], ctx["data"] = list(data.keys()), list(data.values())
    return jt.TemplateResponse("table.html", ctx)

@app.get("/margins/", response_class=HTMLResponse)
async def all_margins(request: Request):
    ctx = {
        "request": request,
        "title": inspect.stack()[0][3],
        "pages": pages,
        "th": ["message"],
        "data": ["No Data Found."],
    }
    body = []
    for uid, user in objs_usr.items():
        data = {"userid": uid}
        mgd = user.get_margins()
        if not mgd:
            continue
        data.update(mgd)
        th, td = list(data.keys()), list(data.values())
        body.append(td)
    if len(body) > 0:
        ctx["th"], ctx["data"] = th, body
    return jt.TemplateResponse("table.html", ctx)

lst = []
for u in objs_usr:
    dictionary = vars(objs_usr[u])
    url = "/positionbook/" + dictionary['_userid']
    dictionary = delete_key_from_dict(dictionary, ["_enctoken", "_broker"])
    dictionary["operations"] = "<a href='" + url + "'>"
    lst.append(dictionary)
if not lst:
    lst = [{'message': 'no data'}]
df = pd.DataFrame(
    data=lst,
    columns=lst[0].keys()
)
df.set_index(['_userid'], inplace=True)
df.index.name = "user id"
if lst_sort_col:
    df.sort_values(by=[lst_sort_col], ascending=True, inplace=True)
ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages,
        "data": df.to_html(escape=False)}
return jt.TemplateResponse("pandas.html", ctx)
"""
