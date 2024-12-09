import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from kite_copier.strategy import Strategy
import os
import sys

print("Current Working Directory:", os.getcwd())
print("Python Path:", sys.path)


@pytest.fixture
def buy_order():
    return {
        "symbol": "NIFTY",
        "average_price": 100,
        "quantity": 10,
        "product": "MIS",
        "exchange": "NSE",
    }


@pytest.fixture
def strategy_instance(buy_order):
    return Strategy(attribs={}, id="test_id", buy_order=buy_order, ltp=100)


def test_set_target(strategy_instance):
    strategy_instance.set_target()
    assert isinstance(
        strategy_instance._bands, np.ndarray
    ), "Bands must be a numpy array."
    assert len(strategy_instance._bands) > 0, "Bands must have at least one value."
    assert (
        strategy_instance._fn == "place_initial_stop"
    ), "Next function should be 'place_initial_stop'."
    assert (
        strategy_instance._stop_price == strategy_instance._bands[0]
    ), "Stop price must be initialized correctly."


def test_update_reaches_target(strategy_instance):
    strategy_instance.set_target()
    strategy_instance._ltp = (
        strategy_instance._bands[-1] + 10
    )  # LTP above the final target
    action = strategy_instance.update()
    assert (
        action == "test_id"
    ), "Strategy should return its ID when final target is reached."


def test_update_moves_stop_price(strategy_instance):
    strategy_instance.set_target()
    strategy_instance._ltp = strategy_instance._bands[1] + 1  # Move to the second band
    action = strategy_instance.update()
    assert (
        action == "hold"
    ), "Strategy should return 'hold' while targets are still being trailed."
    assert (
        strategy_instance._stop_price == strategy_instance._bands[0]
    ), "Stop price should update to the previous band."


def test_update_invalid_bands(strategy_instance):
    strategy_instance._bands = None  # Set invalid bands
    with pytest.raises(ValueError, match="self._bands must be a 1D numpy array."):
        strategy_instance.update()


def test_update_invalid_ltp(strategy_instance):
    strategy_instance.set_target()
    strategy_instance._ltp = None  # Set invalid LTP
    with pytest.raises(ValueError, match="self._ltp must be a scalar value."):
        strategy_instance.update()


@patch("strategy.Helper.place_order", return_value="mock_order_id")
def test_place_initial_stop(mock_place_order, strategy_instance):
    strategy_instance.set_target()
    strategy_instance.place_initial_stop()
    assert (
        strategy_instance._sell_order == "mock_order_id"
    ), "Sell order ID should be set."
    assert (
        strategy_instance._fn == "exit_order"
    ), "Next function should be 'exit_order'."


@patch("strategy.Helper.modify_order", return_value={"status": "modified"})
def test_exit_order(mock_modify_order, strategy_instance):
    strategy_instance._sell_order = "mock_order_id"
    strategy_instance._buy_order = {
        "symbol": "NIFTY",
        "average_price": 100,
        "quantity": 10,
        "product": "MIS",
        "exchange": "NSE",
    }
    strategy_instance.exit_order()
    mock_modify_order.assert_called_once()


def test_run(strategy_instance):
    strategy_instance._fn = "set_target"
    orders = [{"order_id": "mock_order_id"}]
    ltps = {"NIFTY": 105}
    strategy_instance.run(orders=orders, ltps=ltps)
    assert strategy_instance._ltp == 105.0, "LTP should be updated in 'run'."
