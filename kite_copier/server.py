from fastapi import FastAPI, Request, Form
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from user import load_all_users, User
from symbols import dump, read
from constants import logging, S_DATA
from typing import List, Dict, Optional
import inspect
import asyncio


# Load Instrument file.


def return_users() -> Dict[str, User]:
    xls_file = "users_kite.xlsx"
    objs_usr = load_all_users("../../", S_DATA, xls_file)
    return objs_usr


objs_usr = return_users()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ["home", "positions", "orders", "new"]


def get_user_by_id(userid: str) -> User:
    return objs_usr.get(userid, None)


def get_all_orders(userid=None):
    if userid is not None:
        user: User = get_user_by_id(userid)
        if user:
            return user.get_orders()
        else:
            return
    else:
        data = {}
        for user in objs_usr:
            data[user._userid] = user.get_orders()
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
        else:
            dct["orders"] = 0
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


@app.get("/order_cancel/")
def get_order_cancel(request: Request, client_name: str, order_id: str, variety: str):
    obj_client = get_user_by_id(client_name)
    resp = obj_client._broker.order_cancel(order_id, variety)
    logging.info(resp)


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
        if not lst:
            continue
        lst = [{key: dct[key] for key in keys} for dct in lst]
        if any(lst):
            lst = [{"userid": uid, **dct} for dct in lst]
            ctx["body"].extend(lst)
    print(ctx["body"])
    return jt.TemplateResponse("positions.html", ctx)


@app.get("/orders")
def orders(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    ctx["body"] = []
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
    ]
    for uuid, user in objs_usr.items():
        lst = user.get_orders()
        if not lst:
            continue
        lst = [{key: dct[key] for key in keys} for dct in lst]
        if any(lst):
            lst = [{"userid": uuid, **dct} for dct in lst]
            ctx["body"].extend(lst)
    print(ctx["body"])
    return jt.TemplateResponse("orders.html", ctx)


@app.get("/search")
def search(request: Request, sym: str):
    pd = read()
    dt = pd[pd.tradingsymbol.str.startswith(sym.upper())]
    data = dt[:15].to_dict(orient="records")
    return data


@app.get("/modify_orders")
def modify_orders(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}

    symbol = request.query_params.get("symbol")
    side = request.query_params.get("side")
    status = request.query_params.get("status")
    return jt.TemplateResponse("new.html", ctx)


"""
 post
"""


@app.post("/orders/", response_class=RedirectResponse)
async def post_orders(
    request: Request,
    qty: List[int],
    userid: List[str],
    symbol: str = Form(),
    txn: Optional[str] = Form("off"),
    exchange: str = Form(),
    product: str = Form(),
    order: str = Form(),
    price: float = Form(0.0),
    lotsize: int = Form("1"),
    trigger: float = Form(0.0),
):
    """
    places orders for all clients
    """
    side = "BUY" if txn == "on" else "SELL"

    params = {
        "symbol": symbol,
        "exchange": exchange,
        "transactionType": side,
        "orderType": order.upper(),
        "product": product.upper(),
        "price": price,
        "triggerPrice": trigger,
    }

    err = []
    for i, uid in enumerate(userid):
        user = get_user_by_id(uid)
        if user and qty[i] > 0:
            params["quantity"] = qty[i]
            try:
                _ = user.place_order(params)
            except Exception as e:
                err.append(f"{str(e)} occured while placing order for {uid}.")
    if len(err) > 0:
        raise HTTPException(status_code=400, detail=err)
    return "/orders"


@app.on_event("startup")
async def startup_event():
    if __import__("sys").platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    dump()


if __name__ == "__main__":
    __import__("uvicorn").run(app, host="0.0.0.0", port=8000)

"""
    not implemented 
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
            if not pos:
                continue
            data.update(pos)
            th, td = list(data.keys()), list(data.values())
            body.append(td)
        if len(body) > 0:
            ctx["th"], ctx["data"] = th, body
    return jt.TemplateResponse("table.html", ctx)

"""
