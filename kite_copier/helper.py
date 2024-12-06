from traceback import print_exc
import pickle
from constants import logging, S_DATA
from pprint import pprint


class Helper:

    @classmethod
    def api(cls, api):
        cls._api = api
        return cls._api

    @classmethod
    def trades(cls):
        lst = cls._api.trades
        return lst

    @classmethod
    def orders(cls):
        lst = cls._api.orders
        return lst

    @classmethod
    def place_order(cls, kwargs):
        return cls._api.order_place(kwargs)
