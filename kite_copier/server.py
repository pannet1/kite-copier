import asyncio
import inspect
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from constants import S_DATA, logging
from symbols import dump, read
from user import User, load_all_users

# Load Instrument file.


def return_users() -> Dict[str, User]:
    xls_file = "users_kite.xlsx"
    objs_usr = load_all_users("../../", S_DATA, xls_file)
    return objs_usr


objs_usr = return_users()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ["home", "positions", "orders", "all", "new"]


def get_user_by_id(userid: str) -> User:
    return objs_usr.get(userid, None)


def get_all_orders(userid=None, status=None):
    if userid is not None:
        user: User = get_user_by_id(userid)
        if user:
            return user.get_orders(status=status)
        else:
            return
    else:
        data = []
        for user in objs_usr.values():
            order = user.get_orders(status=status)
            if order:
                data.extend(order[:])
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


@app.get("/order_cancel")
def get_order_cancel(request: Request, client_name: str, order_id: str):
    obj_client = get_user_by_id(client_name)
    kwargs = dict(order_id=order_id, variety="regular")
    try:
        # _ = obj_client._broker.order_cancel(**kwargs)
        d = obj_client._broker.kite.cancel_order(**kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        return JSONResponse(content={"status": "success"})


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
    statuses = ["OPEN", "TRIGGER PENDING"]
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
            lst = [
                {"userid": uuid, **dct}
                for dct in lst
                if dct["status"].upper() in statuses
            ]
            ctx["body"].extend(lst)
    return jt.TemplateResponse("orders.html", ctx)


@app.get("/all")
def all(request: Request):
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
    return jt.TemplateResponse("orders.html", ctx)


@app.get("/search")
def search(request: Request, sym: str):
    pd = read()
    dt = pd[pd.tradingsymbol.str.startswith(sym.upper())]
    data = dt[:15].to_dict(orient="records")
    return data


@app.get("/bulk_modify_order", response_class=HTMLResponse)
async def get_bulk_modify_order(
    request: Request,
    exchange: str,
    tradingsymbol: str,
    # symboltoken: str,
    transactiontype: str,
    producttype: str,
    status: str,
    ordertype: str,
):
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    subs = dict(
        exchange=exchange,
        tradingsymbol=tradingsymbol,
        # symboltoken=symboltoken,
        transaction_type=transactiontype,
        order_type=ordertype,
        status=status,
        product=producttype,
    )
    data = get_all_orders(status="open")
    if data:
        fdata = []
        for ord in data:
            success = True
            for k, v in subs.items():
                if ord.get(k) != v:
                    success = False
                    break
            if success:
                fdata.append(ord)
        if any(fdata):
            ctx["th"], ctx["data"] = [
                "Client",
                "OrderID",
                "Price/Trigger",
                "Qty",
            ], fdata
            # _, flt_ltp = get_ltp(subs["exchange"], subs["tradingsymbol"], subs["symboltoken"])
            # subs["price"] = flt_ltp[0][0]

    ctx["subs"] = [subs]
    return jt.TemplateResponse("orders_modify.html", ctx)


"""
 post
"""


@app.post("/bulk_modify_order")
async def post_bulk_modified_order(
    request: Request,
    client_name: List[str],
    order_id: List[str],
    quantity: List[str],
    txn_type: str = Form(),
    exchange: str = Form(),
    symboltoken: str = Form(),
    tradingsymbol: str = Form(),
    otype: int = Form("0"),
    producttype: str = Form(),
    triggerprice: str = Form(),
    price: str = Form(),
):
    """
    post modified orders in bulk
    """
    variety = "regular"
    if otype == 1:
        ordertype = "LIMIT"
    elif otype == 2:
        ordertype = "MARKET"
    elif otype == 3:
        ordertype = "SL"
    elif otype == 4:
        ordertype = "SL-M"

    try:
        for i, uid in enumerate(client_name):
            user = get_user_by_id(uid)
            if not user:
                continue
            params = dict(
                variety=variety,
                order_id=order_id[i],
                quantity=quantity[i],
                price=price,
                order_type=ordertype,
                trigger_price=triggerprice,
            )
            d = user._broker.kite.modify_order(**params)
    except Exception as e:
        return JSONResponse(
            content={"Error bulk order modifying": str(e)}, status_code=400
        )
    else:
        return RedirectResponse("/orders", status_code=status.HTTP_303_SEE_OTHER)


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
    return RedirectResponse("/orders", status_code=status.HTTP_303_SEE_OTHER)


@app.on_event("startup")
async def startup_event():
    if __import__("sys").platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    dump()


if __name__ == "__main__":
    __import__("uvicorn").run(app, host="0.0.0.0", port=8000)
