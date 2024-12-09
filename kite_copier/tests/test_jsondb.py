import pytest
from unittest.mock import MagicMock, patch
from jsondb import Jsondb


@pytest.fixture
def mock_trades():
    """Sample trades from API."""
    return [
        {
            "order_id": "101",
            "broker_timestamp": "2024-12-06T09:30:00",
            "symbol": "AAPL",
        },
        {
            "order_id": "102",
            "broker_timestamp": "2024-12-06T09:35:00",
            "symbol": "GOOG",
        },
    ]


@pytest.fixture
def mock_file_data():
    """Sample orders saved in the file."""
    return [{"_id": "101", "entry": {"symbol": "AAPL"}}]


@pytest.fixture
def mock_completed_trades():
    """Sample completed trades."""
    return ["102"]


@pytest.fixture
def mock_orders_file(tmp_path):
    """Temporary file path for testing."""
    return tmp_path / "orders.json"


# Test setup_db
@patch("constants.O_FUTL.write_file")
def test_setup_db(mock_write_file, mock_orders_file):
    Jsondb.setup_db(mock_orders_file)
    mock_write_file.assert_called_once_with(filepath=mock_orders_file, content=[])


# Test write
@patch("constants.O_FUTL.write_file")
def test_write(mock_write_file, mock_orders_file):
    Jsondb.F_ORDERS = mock_orders_file
    content = [{"_id": "101", "entry": {"symbol": "AAPL"}}]
    Jsondb.write(content)
    mock_write_file.assert_called_once_with(filepath=mock_orders_file, content=content)


# Test read
@patch(
    "constants.O_FUTL.json_fm_file",
    return_value=[{"_id": "101", "entry": {"symbol": "AAPL"}}],
)
def test_read(mock_json_fm_file, mock_orders_file):
    Jsondb.F_ORDERS = mock_orders_file
    data = Jsondb.read()
    mock_json_fm_file.assert_called_once_with(mock_orders_file)
    assert data == [{"_id": "101", "entry": {"symbol": "AAPL"}}]


# Test filter_orders
@patch("constants.O_FUTL.json_fm_file")
def test_filter_orders(
    mock_json_fm_file,
    mock_trades,
    mock_file_data,
    mock_completed_trades,
    mock_orders_file,
):
    mock_json_fm_file.return_value = mock_file_data
    Jsondb.F_ORDERS = mock_orders_file

    # Filter the orders
    filtered_orders = Jsondb.filter_orders(mock_trades, mock_completed_trades)

    # Validate filtered output
    assert len(filtered_orders) == 1
    assert filtered_orders[0]["id"] == "102"  # Only non-matching order is returned
    assert filtered_orders[0]["entry"]["symbol"] == "GOOG"
