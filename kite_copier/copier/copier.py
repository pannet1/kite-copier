from typing import Dict
import pandas as pd
from toolkit.datastruct import Datastruct


def differance(s):
    """
    calculate the differance quantity required
    given the target and follower positions
    """
    value = s['tgt'] - s['flwr']
    return str(int(value))


class Copier():

    def __init__(self, lotsize: Dict) -> None:
        self.lst_filter = ['exchange',
                           'symbol',
                           'product',
                           'quantity']
        self.lotsize = lotsize
        self.ds = Datastruct()

    def _rounded_lot(self, df: pd.DataFrame):
        """
        rounds quantity product to the nearest lot
        """
        if df.quantity == 0:
            return df.quantity
        for k, v in self.lotsize.items():
            if (df.symbol).startswith(k):
                tmp = round(df.quantity / v)
                return tmp * v
        return df.quantity

    def filter_pos(self, pos):
        """
        filter position dictionaries
        """
        lst = []
        for p in pos:
            dct = self.ds.fltr_dct_by_key(p, self.lst_filter)
            lst.append(dct)
        return lst

    def fltr_ign(self, df, dct_blk):
        if df.empty:
            return df
        df_blk = pd.DataFrame(data=[dct_blk])
        df_opp = df.merge(df_blk, how='outer', indicator=True)
        df_act = df_opp[(df_opp._merge == 'left_only')].drop('_merge', axis=1)
        return df_act

    def set_ldr_df(self, lst: list, fltr_dcts: list):
        df_ldr = pd.DataFrame(data=lst)
        print(df_ldr)
        if not df_ldr.empty:
            for fltr_dct in fltr_dcts:
                df_ldr = self.fltr_ign(df_ldr, fltr_dct)

        self.df_ldr = df_ldr
        print("===  LEADER ===")
        print(self.df_ldr)

    def get_tgt_df(self, multiply: float) -> pd.DataFrame:
        """
        calculate target position required given the multiplier
        """
        print(f"\n=== TARGET after multiplier {multiply} ===")
        df_tgt = self.df_ldr.copy()
        if not df_tgt.empty:
            df_tgt['quantity'] = df_tgt.quantity * multiply
            df_tgt['quantity'] = df_tgt.apply(
                self._rounded_lot, axis=1).astype(int)
        print(df_tgt)
        return df_tgt

    def get_diff_pos(self,  userid: str, tgt: pd.DataFrame, lst_flwr_pos):
        """
        calculate required order quantity given the target and
        current follower position
        """
        tgt = tgt.rename(columns={'quantity': 'tgt'})
        tgt['userid'] = userid
        merg = tgt.copy()
        merg['flwr'] = 0
        if any(lst_flwr_pos):
            flwr = pd.DataFrame(data=lst_flwr_pos)
            print("\n")
            print("====  FOLLOWER ====")
            print(flwr)
            flwr = flwr.rename(columns={'quantity': 'flwr'})
            merg = pd.merge(
                flwr, tgt, on=['symbol', 'exchange', 'product'], how='outer')
            if merg['tgt'].isnull().values.any():
                print("\n=== we have FOLLOWER positions without LEADER ===")
                merg.dropna(subset=["tgt"], inplace=True)
            if merg['flwr'].isnull().values.any():
                print("\n=== we have LEADER positions without FOLLOWER ===")
                merg['flwr'] = merg['flwr'].fillna(0)
        merg['quantity'] = merg.apply(differance, axis=1)
        merg['flwr'] = merg.flwr.astype(int)
        print("\nFOLLOWER and TARGET combined view")
        print(merg)
        return merg
