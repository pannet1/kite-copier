from _typeshed import NoneType
from pickle import NONE
from constants import logging, O_SETG
from helper import Helper
from traceback import print_exc

from kite_copier.aqd468 import main
import numpy as np


class TrailingStopLoss:
    def __init__(self, entry_price, threshold_pct, targets):
        self.entry_price = entry_price
        self.threshold = (threshold_pct / 100) * entry_price
        self.targets = targets

        # Generate bands (merging initial bands)
        self._bands = np.concatenate(
            (
                [entry_price - self.threshold],  # Merged band_0 starts from this point
                np.linspace(
                    entry_price,
                    entry_price + (targets - 2) * self.threshold,
                    num=targets - 1,
                ),
            )
        )
        # Initialize state
        # Initialize state
        self._current_band_idx = 0
        self.stop_price = self._bands[0]

    def update(self, self._ltp):
        # Find the new band index for the current LTP
        new_band_idx = np.searchsorted(self._bands, self._ltp, side="right") - 1

        if new_band_idx > self._current_band_idx:
            # LTP moved to a higher band
            self._current_band_idx = new_band_idx
            if self._current_band_idx == self.targets:
                # Target reached
                print(f"LTP {ltp}: Target reached. Exit at {self._ltp}")
                return "exit"
            else:
                self.stop_price = self._bands[self._current_band_idx]  # Update stop price
                print(
                    f"LTP {ltp}: Moved to Band {self._current_band_idx}. New stop: {self.stop_price}"
                )
        elif new_band_idx < self._current_band_idx:
            # LTP moved to a lower band (optional warning)
            print(
                f"LTP {self._ltp}: Dropped to Band {new_band_idx}. Current stop remains: {self.stop_price}"
            ]            )
        else:
            # No band change
            print(f"LTP {self._ltp}: No band change. Current stop: {self.stop_price}")

        return "hold"


# Example usage
self._fill_price = 100
threshold_pct = 5
targets = 10

# Initialize the trailing stop loss manager
tsl = TrailingStopLoss(self._fill_price, threshold_pct, targets)

# Simulate LTP updates
ltp_values = [94, 96, 99, 103, 108, 112, 116, 123, 135, 145]
for ltp in ltp_values:
    action = tsl.update(ltp)
    if action == "exit":
        break


class Strategy:
    def __init__(self, attribs: dict, id: str, buy_order: dict, symbol_info: dict):
        if any(attribs):
            self.__dict__.update(attribs)
        else:
            # settings threshold
            threshold = 5
            targets = 3
            self._id = id
            self._buy_order = buy_order
            self._symbol = buy_order["symbol"]
            self._fill_price = float(buy_order["average_price"])
            self._ltp = float(symbol_info["ltp"])
            self._threshold = threshold * self._fill_price / 100
            self._targets = targets
            self._current_band_idx = 0
            self._sell_order = ""
            self._orders = []
            self._stop_price = None
            self._fn = "set_threshold"

    def set_target(self):
        try:
            # Generate bands (merging initial bands)
            self._bands = np.linspace(
                self._fill_price - self._threshold,
                self._fill_price + self._targets + (self._targets - 2) * self._threshold,
                num=self._targets
            )
            self._stop_price = self._bands[0]
            self._fn = "place_sell_order"
        except Exception as e:
            print_exc()
            print(f"{e} while set target")

    def update(self):
        # Find the new band index for the current LTP
        # TODO explain searcsorted
        new_band_idx = np.searchsorted(self._bands, self._ltp, side="right") - 1

        if new_band_idx > self._current_band_idx:
            # LTP moved to a higher band
            self._current_band_idx = new_band_idx
            if self._current_band_idx == self._targets:
                # Target reached, modify stop to exit at market order``
                print(f"LTP {self._ltp}: Final Target reached. Exit at T{self._targets}")
                return self._id
            elif self._current_band_idx >2:
                self.stop_price = self._bands[self._current_band_idx - 1]  # Update stop price
                print(f"LTP {ltp}: Moved to Band {self._current_band_idx}. New stop: {self.stop_price}")
        elif new_band_idx < self._current_band_idx:
            # LTP moved to a lower band (optional warning)
            print(f"LTP {ltp}: Dropped to Band {new_band_idx}. Current stop remains: {self.stop_price}")
        else:
            # No band change
            print(f"LTP {ltp}: No band change. Current stop: {self.stop_price}")

        return "hold"


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
                price=self._threshold,
                trigger_price=0,
                order_type="LMT",
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


if __name__ == "main":
# Example usage
    entry_price = 100
    threshold_pct = 5
    num_bands = 10

# Initialize the trailing stop loss manager
    tsl = TrailingStopLoss(entry_price, threshold_pct, num_bands)

# Simulate LTP updates
    ltp_values = [94, 96, 99, 103, 108, 112, 116, 123, 135, 145]
    for ltp in ltp_values:
        action = tsl.update(ltp)
        if action == "exit":
            break

