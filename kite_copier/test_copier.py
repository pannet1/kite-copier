from copier import Copier
from tests.big import test_trades as big
from tests.small import test_trades as small
import pandas as pd


maxlots = {'NIFTY': 900, 'BANKNIFTY': 25, 'FINNIFTY': 40}
ignore = [
    {'product': 'NRML'},
    {'product': 'CNC'},
    {'symbol': 'HDFC-EQ', 'exchange': 'NSE'}
]
ORDER_TYPE = 'LIMIT'
dct_lots = {'NIFTY': 50, 'BANKNIFTY': 25}
cop = Copier(dct_lots)

lst_ldr = cop.filter_pos(big)
cop.set_ldr_df(lst_ldr, ignore)
# we show position of flwrs only
# if there is leader positions
i = 5
df_pos = pd.DataFrame()
if not cop.df_ldr.empty:
    for a in [[], small]:
        # pass the flwr multiplier from xls
        df_tgt = cop.get_tgt_df(2.0125)
        dct_flwr = cop.filter_pos(a)
        # pass the user id from txls
        i += 1
        df_ord = cop.get_diff_pos(i, df_tgt, dct_flwr)
        df_ord = df_ord[df_ord.quantity != '0']
        if not df_ord.empty:
            df_pos = df_ord if df_pos.empty else pd.concat(
                [df_pos, df_ord], sort=True)


def multiply(multiplied):
    for m in multiplied:
        try:
            quantity = int(m.get('quantity', 0))
            if quantity == 0:
                print("quantity cannot be zero")
            dir = 1 if quantity > 0 else -1
            """
            ensure that the symbol is in the max lots list
            if not iceberg is zero
            """
            if ORDER_TYPE == 'LIMIT':
                m['price'] = 11.11
            m['order_type'] = ORDER_TYPE
            if m['exchange'] == 'NFO':
                symbol = next(k for k, v in maxlots.items()
                              if m['symbol'].startswith(k))
                iceberg = maxlots.get(symbol, 0)
                if iceberg > 0 and abs(quantity) >= iceberg:
                    remainder = int(abs(quantity % iceberg) * dir)
                    if abs(remainder) > 0:
                        m['quantity'] = remainder
                        print(f' placing order for reminder {remainder}')
                        times = int(abs(quantity) / iceberg)
                        for i in range(times):
                            m['quantity'] = iceberg * dir
                            print(f' placing order for iceberg {iceberg}')
            else:
                m['quantity'] = int(quantity)
                print(f"place order for equity {quantity}")
        except Exception as e:
            print(e)
            break


data = {}
data['positions'] = df_pos.to_dict('records')
print("positon returned finally")
print(df_pos)
multiply(data['positions'])
