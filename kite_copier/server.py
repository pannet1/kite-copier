from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from toolkit.logger import Logger
import inspect
from user import load_all_users

sec_dir = "../../../"
logging = Logger(20, sec_dir + "kite-copier.log")  # 2nd param 'logfile.log'


def return_users():
    xls_file = "users_kite.xlsx"
    obj_ldr, objs_usr = load_all_users(sec_dir, xls_file)
    return obj_ldr, objs_usr


def delete_key_from_dict(dictionary, key_list):
    for key in key_list:
        if key in dictionary:
            del dictionary[key]
    return dictionary


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
jt = Jinja2Templates(directory="templates")
pages = ['home']
obj_ldr, objs_usr = return_users()


@ app.get("/dummy", response_class=HTMLResponse)
async def home(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3]}
    return jt.TemplateResponse("index.html", ctx)


@ app.get("/", response_class=HTMLResponse)
async def users(request: Request):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    ctx['th'] = ['message']
    ctx['data'] = ["no data"]
    body = []
    for keys, row in objs_usr.items():
        th = ['user id', 'target', 'max loss', 'disabled', 'orders', 'pnl']
        td = [
            row._userid,
            row._target,
            row._max_loss,
            row._disabled,
        ]
        orders = row._broker.orders
        completed_count = 0
        if isinstance(orders, list):
            for item in orders:
                if isinstance(item, dict) and item.get('orderstatus') == 'complete':
                    completed_count += 1
        td.append(completed_count)
        lst_pos = row._broker.positions
        sum = 0
        if isinstance(lst_pos, list):
            for dct in lst_pos:
                sum += int(float(dct.get('pnl', 0)))
            td.append(sum)
            body.append(td)
    if len(body) > 0:
        ctx['th'] = th
        ctx['data'] = body
    return jt.TemplateResponse("users.html", ctx)

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


@ app.get("/positionbook/{user_id}", response_class=HTMLResponse)
async def positions(request: Request, user_id):
    ctx = {"request": request, "title": inspect.stack()[0][3], 'pages': pages}
    ctx['tx'] = ['message']
    ctx['data'] = ['no data']
    body = []
    for keys, rows in objs_usr.items():
        lst_positions = rows._broker.positions
        for f_dct in lst_positions:
            k = f_dct.keys()
            th = list(k)
            v = f_dct.values()
            td = list(v)
            body.append(td)
        if len(body) > 0:
            ctx['th'] = th
            ctx['data'] = body
    return jt.TemplateResponse("table.html", ctx)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
