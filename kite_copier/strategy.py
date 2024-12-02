from constants import logging, O_SETG
from helper import Helper
from traceback import print_exc


class Strategy:
    def __init__(self, attribs: dict, id: str, buy_order: dict, symbol_info: dict):
        if any(attribs):
            self.__dict__.update(attribs)
        else:
            self._id = id
            self._buy_order = buy_order
            self._symbol = buy_order["symbol"]
            self._fill_price = float(buy_order["fill_price"])
            self._low = float(symbol_info["low"])
            self._ltp = float(symbol_info["ltp"])
            self._target = O_SETG["trade"]["target"]
            self._stop = float(symbol_info["low"])
            self._sell_order = ""
            self._orders = []
            self._fn = "set_target"

    def set_target(self):
        try:
            target_buffer = self._target * self._fill_price / 100
            target_virtual = self._fill_price + target_buffer
            if self._fill_price < self._low:
                self._target = min(target_virtual, self._low)
                self._stop = 0.00
            else:
                self._target = target_virtual

            self._target = round(self._target / 0.05) * 0.05
            self._fn = "place_sell_order"
        except Exception as e:
            print_exc()
            print(f"{e} while set target")

    def is_id_in_list(self, order_id):
        try:
            for order in self._orders:
                if order_id == order["order_id"]:
                    return True
            return False
        except Exception as e:
            logging.error(f"{e} get order from book")
            print_exc()

    def place_sell_order(self):
        try:
            sargs = dict(
                symbol=self._symbol,
                quantity=abs(int(self._buy_order["quantity"])),
                product=self._buy_order["product"],
                side="S",
                price=self._target,
                trigger_price=0,
                order_type="LMT",
                exchange=self._buy_order["exchange"],
                tag="exit",
            )
            logging.debug(sargs)
            self._sell_order = Helper.one_side(sargs)
            if self._sell_order is None:
                raise RuntimeError(
                    f"unable to get order number for {self._buy_order}. please manage"
                )
            else:
                self._fn = "exit_order"
        except Exception as e:
            logging.error(f"{e} whle place sell order")
            print_exc()

    def exit_order(self):
        try:
            if self.is_id_in_list(self._sell_order):
                logging.info(
                    f"{self._symbol} target order {self._sell_order} is reached"
                )
                return self._id
            elif self._ltp < self._stop:
                args = dict(
                    symbol=self._symbol,
                    order_id=self._sell_order,
                    exchange=self._buy_order["exchange"],
                    quantity=abs(int(self._buy_order["quantity"])),
                    price_type="MARKET",
                    price=0.00,
                )
                resp = Helper.modify_order(args)
                logging.debug(f"order id: {args['order_id']} {resp}")
                return self._id

        except Exception as e:
            logging.error(f"{e} while exit order")
            print_exc()

    def run(self, orders, ltps):
        try:
            self._orders = orders
            ltp = ltps.get(self._symbol, None)
            if ltp is not None:
                self._ltp = float(ltp)
            getattr(self, self._fn)()
        except Exception as e:
            logging.error(f"{e} in run for buy order {self._id}")
            print_exc()
