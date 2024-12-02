from traceback import print_exc
import pickle
from constants import logging, S_DATA


class Helper:

    def __init__(self, userid: str):
        pklfile = f"{S_DATA}{userid}.pkl"
        with open(pklfile, "rb") as pkl:
            self._api = pickle.load(pkl)
