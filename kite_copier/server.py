from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from toolkit.logger import Logger
from toolkit.fileutils import Fileutils
from user import load_all_users, User, load_symbol_data
from typing import List, Dict, Optional
import starlette.status as status
import inspect

data_dir = "../data/"
sec_dir = "../../"

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
            if not pos:
                continue
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
        if not lst:
            continue
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
        for odr in odrs:
            if not odr:
                continue
            th, td = list(odr.keys()), list(odr.values())
            body.append(td)
        if len(body) > 0:
            ctx["th"], ctx["data"] = th, body
    return jt.TemplateResponse("table.html", ctx)


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
async def search(request: Request, sym: str):
    # dt = pd[pd.tradingsymbol.str.contains(sym.upper())]
    dt = pd[pd.tradingsymbol.str.startswith(sym.upper())]
    data = dt[:15].to_dict(orient="records")
    return data


"""
 post
"""


@app.post("/orders/")
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
    ctx = {"request": request, "title": inspect.stack()[0][3], "pages": pages}
    mh, md, th, td = [], [], [], []
    side = "BUY" if txn == "on" else "SELL"
    if not order.upper() in ("MARKET", "LIMIT", "SL", "SL-M"):
        # here can return error to user if orderType is not valid
        pass

    if not product.upper() in ("NRML", "MIS", "CNC"):
        # here can return error to user if orderType is not valid
        pass

    params = {
        "symbol": symbol,
        "exchange": exchange,
        "transactionType": side,
        "orderType": order.upper(),
        "product": product.upper(),
        "price": price,
        "triggerPrice": trigger,
    }

    data = []
    for i, uid in enumerate(userid):
        user = get_user_by_id(uid)
        if user and qty[i] > 0:
            params["quantity"] = qty[i]
            try:
                dt = user.place_order(params)
                data.append(dt)
            except Exception as e:
                data = str(e)
                break
            # if len(mh) > 0:
            # ctx["mh"], ctx["md"] = mh, md
            # if len(th) > 0:
            # ctx["th"], ctx["data"] = th, td
        # return jt.TemplateResponse("table.html", ctx)
    return HTMLResponse(str(data))
    # else:
    # return RedirectResponse("/orders", status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

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
