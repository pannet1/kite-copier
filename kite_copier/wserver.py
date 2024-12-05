from constants import logging


class Wserver:

    def list_to_dict(self, ticks):
        for dct in ticks:
            self.ltp[dct["instrument_token"]] = dct["last_price"]

    def __init__(self, kite):
        self.ltp = {}
        self.new_token = None
        self.kws = kite.kws()
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error
        self.kws.on_reconnect = self.on_reconnect
        self.kws.on_noreconnect = self.on_noreconnect

        # Infinite loop on the main thread. Nothing after this will run.
        # You have to use the pre-defined callbacks to manage subscriptions.
        self.kws.connect(threaded=True)

    def on_ticks(self, ws, ticks):
        if self.new_token:
            ws.subscribe([self.new_token])
            ws.set_mode(ws.MODE_LTP, [self.new_token])
        self.list_to_dict(ticks)

    def on_connect(self, ws, response):
        # self.tokens = [v for k, v in nse_symbols.items() if k == "instrument_token"]
        instrument_token = [738561, 5633]
        ws.subscribe(instrument_token)
        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_LTP, instrument_token)
        logging.debug(f"on connect: {response}")

    def on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        logging.warning("ws closed with code {}: {}".format(code, reason))
        # ws.stop()

    def on_error(self, ws, code, reason):
        # Callback when connection closed with error.
        logging.error(
            "Connection error: {code} - {reason}".format(code=code, reason=reason)
        )

    def on_reconnect(self, ws, attempts_count):
        # Callback when reconnect is on progress
        logging.warning("Reconnecting: {}".format(attempts_count))

    # Callback when all reconnect failed (exhausted max retries)
    def on_noreconnect(self, ws):
        logging.error("Reconnect failed.")
