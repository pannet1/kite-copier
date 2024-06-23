from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from toolkit.logger import Logger
from user import load_all_users, User
from typing import List, Dict
import inspect

sec_dir = "../../"
logging = Logger(20, sec_dir + "kite-copier.log")  # 2nd param 'logfile.log'


def return_users() -> Dict[User]:
    xls_file = "users_kite.xlsx"
    objs_usr = load_all_users(sec_dir, xls_file)
    return objs_usr


def delete_key_from_dict(dictionary, key_list):
    for key in key_list:
        if key in dictionary:
            del dictionary[key]
    return dictionary


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ['home']
objs_usr = return_users()


def get_user_by_id(userid: str) -> User:
    return objs_usr.get(userid, None)

def get_all_orders(userid=None):
    if userid is not None:
        user: User = get_user_by_id(userid)
        if user: return user.get_orders()
        else: return
    else:
        data = {}
        for user in objs_usr:
            data[user._userid] = user.get_orders()
        return data



@ app.get("/dummy", response_class=HTMLResponse)
async def home(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3]}
    return jt.TemplateResponse("index.html", ctx)


@ app.get("/", response_class=HTMLResponse)
async def users(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': ['No Data Found.']}
    body = []
    for user in objs_usr.values():
        th = ['Userid', 'Target', 'MaxLoss', 'Disable', 'CompletedOrders', 'PnL', 'Net-Margin (Equity)']
        td = [user._userid, user._target, user._max_loss, user._disabled]
        # Completed Orders Count.
        orders = user.get_orders()
        completed = 0
        if isinstance(orders, list):
            for order in orders:
                if isinstance(order, dict) and 'complete' in order.get('status').lower():
                    completed += 1
        td.append(completed)
        # Pnl Count.
        poss = user.get_positions()
        pnl = 0
        if isinstance(poss, list):
            for pos in poss:
                pnl += float(pos.get('pnl', 0))
            td.append(pnl)
        # Equity Net-Margin.
        marg = user.get_margins().get('equity', {}).get('net', 0.0)
        td.append(marg)        
        body.append(td)
    if len(body) > 0:
        ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("users.html", ctx)


@ app.get("/margin/{userid}", response_class=HTMLResponse)
async def marginbook(request: Request, userid: str):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': [f'No Data Found for {userid}.']}
    user = get_user_by_id(userid)
    if user:
        data = {"userid": userid}
        mgd = user.get_margins()
        if mgd:
            data.update(mgd)
            ctx['th'], ctx['data'] = list(data.keys()), list(data.values())
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/margins/", response_class=HTMLResponse)
async def all_margins(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': ['No Data Found.']}
    body = []
    for uid, user in objs_usr.items():
        data = {"userid": uid}
        mgd = user.get_margins().get("equity", {})
        if not mgd: continue
        data.update(mgd)
        th, td = list(data.keys()), list(data.values())
        body.append(td)
    if len(body) > 0: ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/position/{userid}", response_class=HTMLResponse)
async def positionbook(request: Request, userid: str):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': [f'No Data Found for {userid}.']}
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
        if len(body) > 0: ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("table.html", ctx)


@ app.get("/positions/", response_class=HTMLResponse)
async def all_positions(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': ['No Data Found.']}
    body = []
    for uid, user in objs_usr.items():
        data = {"userid": uid}
        poss = user.get_positions()
        for pos in poss:
            if not pos: continue
            data.update(pos)
            th, td = list(data.keys()), list(data.values())
            body.append(td)
    if len(body) > 0: ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("table.html", ctx)


@app.get("/order/{userid}", response_class=HTMLResponse)
async def orderbook(request: Request, userid: str):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': [f'No Data Found for {userid}.']}
    user = get_user_by_id(userid)
    if user:
        body = []
        odrs = user.get_orders()
        for odr in odrs:
            if not odr: continue
            th, td = list(odr.keys()), list(odr.values())
            body.append(td)
        if len(body) > 0: ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("table.html", ctx)


@app.get("/orders/", response_class=HTMLResponse)
async def all_orders(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages, 'th': ['message'], 'data': ['No Data Found.']}
    body = []
    for user in objs_usr.values():
        odrs = user.get_orders()
        for odr in odrs:
            if not odr: continue
            th, td = list(odr.keys()), list(odr.values())
            body.append(td)
    if len(body) > 0: ctx['th'], ctx['data'] = th, body
    return jt.TemplateResponse("table.html", ctx)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


"""
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
