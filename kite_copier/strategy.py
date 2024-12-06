from constants import logging, O_SETG
from helper import Helper
from traceback import print_exc
import numpy as np


class Strategy:
    def __init__(self, attribs: dict, id: str, buy_order: dict, ltp: float):
        if any(attribs):
            self.__dict__.update(attribs)
        else:
            # settings
            threshold = 5  # percentage
            targets = 6  # total targets for example T6
            self._id = id
            self._buy_order = buy_order
            self._symbol = buy_order["symbol"]
            self._fill_price = buy_order["average_price"]
            self._ltp = ltp
            self._threshold = threshold * self._fill_price / 100
            self._targets = targets
            self._current_target = 0
            self._sell_order = ""
            self._orders = []
            self._stop_price = self._fill_price - self._threshold * 2
            self._fn = "set_target"

    def set_target(self):
        try:
            # Generate bands (merging initial bands)
            self._bands = np.concatenate(
                (
                    [self._fill_price - self._threshold * 2],
                    np.linspace(
                        self._fill_price + self._threshold,
                        self._fill_price + self._targets * self._threshold,
                        num=self._targets,
                    ),
                )
            )
            self._stop_price = self._bands[0]
            self._fn = "place_initial_stop"
            print(self._bands)
        except Exception as e:
            print_exc()
            print(f"{e} while set target")

    def update(self):
        try:
            if self.is_order_completed():
                logging.info("trail stopped")
                return self._id

            # LTP moved to a higher band
            if self._ltp > self._bands[-1]:
                # Target reached, modify stop to exit at market order
                # TODO modify stop to target
                print(f"LTP {self._ltp} reached final target{self._bands[-1]}")
                return self._id

            if not isinstance(self._bands, np.ndarray) or self._bands.ndim != 1:
                raise ValueError("self._bands must be a 1D numpy array.")
            if not np.isscalar(self._ltp):
                raise ValueError("self._ltp must be a scalar value.")

            # Find the new band index for the current LTP
            new_target = np.searchsorted(self._bands, self._ltp, side="right") - 1

            if new_target > self._current_target:
                if self._current_target == 0:
                    self._stop_price = self._fill_price
                else:
                    self._stop_price = self._bands[self._current_target]

                self._current_target = new_target
                print(
                    f"LTP {self._ltp}: is above Target {new_target}. New stop: {self._stop_price}"
                )
            elif new_target < self._current_target:
                # LTP moved to a lower band (optional warning)
                print(
                    f"LTP {self._ltp}: Dropped below Target {new_target}. Current stop remains: {self._stop_price}"
                )
            else:
                # LTP moved to a lower band (optional warning)
                print(f"LTP {self._ltp}: Stop remains unchanged")

            return "hold"
        except Exception as e:
            logging.error(f"{e} in update")
            print_exc()

    def place_initial_stop(self):
        try:
            sargs = dict(
                symbol=self._symbol,
                quantity=abs(int(self._buy_order["quantity"])),
                product=self._buy_order["product"],
                side="S",
                price=0,
                trigger_price=0,
                order_type="SLM",
                exchange=self._buy_order["exchange"],
                tag="exit",
            )
            logging.debug(sargs)
            self._sell_order = Helper.place_order(sargs)
            if self._sell_order is None:
                raise RuntimeError(
                    f"unable to get order number for {self._buy_order}. please manage"
                )
            else:
                self._fn = "exit_order"
        except Exception as e:
            logging.error(f"{e} whle place sell order")
            print_exc()

    def is_order_completed(self):
        try:
            for order in self._orders:
                if self._sell_order == order["order_id"]:
                    logging.info(f"{self._symbol} order {self._sell_order} is complete")
                    return True
        except Exception as e:
            logging.error(f"{e} get order from book")
            print_exc()

    def exit_order(self):
        try:
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


if __name__ == "__main__":
    try:
        entry_price = 100
        buy_order = {
            "symbol": "NIFTY",
            "average_price": entry_price,
            "quantity": 10,
            "product": "MIS",
            "exchange": "NSE",
        }

        tsl = Strategy(attribs={}, id=1, buy_order=buy_order, ltp=100)

        # Simulate LTP updates
        ltp_values = [94, 96, 99, 103, 108, 112, 116, 123, 135, 145]
        for ltp in ltp_values:
            tsl.set_target()
            tsl._ltp = ltp
            action = tsl.update()
            if action == tsl._id:
                print("Exiting strategy.")
                break
    except Exception as e:
        print(e)
        print_exc()