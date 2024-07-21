from constants import S_DATA, O_FUTL
import pandas as pd


fpath = S_DATA + "instrument.csv"


def dump():
    if O_FUTL.is_file_not_2day(fpath):
        # Download file & save it.
        url = "https://api.kite.trade/instruments/NFO"
        print("Downloading & Saving Symbol file...")
        df = pd.read_csv(url, on_bad_lines="skip")
        df.fillna(pd.NA, inplace=True)
        df.sort_values(
            ["instrument_type", "exchange"], ascending=[False, False], inplace=True
        )
        df.to_csv(fpath, index=False)


def read():
    df = pd.read_csv(fpath, on_bad_lines="skip")
    df.fillna(pd.NA, inplace=True)
    return df
