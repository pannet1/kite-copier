import pendulum as pdlm
from unittest.mock import patch


def test_order_time_future():
    # Given order timestamp
    order_timestamp = "11:37:02"

    # Mock current time to ensure test consistency
    mock_current_time = pdlm.datetime(2023, 12, 19, 11, 36, 58, tz="Asia/Kolkata")

    # Parse the order timestamp into a Pendulum time object
    order_time = pdlm.parse(order_timestamp, strict=False, tz="Asia/Kolkata")

    # Add today's date to the order time
    order_time = order_time.replace(
        year=mock_current_time.year,
        month=mock_current_time.month,
        day=mock_current_time.day,
    )

    # Validate that order time is correctly identified as in the future
    with patch("pendulum.now", return_value=mock_current_time):
        assert (
            order_time > mock_current_time
        ), f"Expected {order_time=} > {mock_current_time=}"


def test_order_time_past():
    # Given order timestamp
    order_timestamp = "11:37:02"

    # Mock current time to ensure test consistency
    mock_current_time = pdlm.datetime(2023, 12, 19, 11, 37, 5, tz="Asia/Kolkata")

    # Parse the order timestamp into a Pendulum time object
    order_time = pdlm.parse(order_timestamp, strict=False, tz="Asia/Kolkata")

    # Add today's date to the order time
    order_time = order_time.replace(
        year=mock_current_time.year,
        month=mock_current_time.month,
        day=mock_current_time.day,
    )

    # Validate that order time is correctly identified as in the past
    with patch("pendulum.now", return_value=mock_current_time):
        assert (
            order_time < mock_current_time
        ), f"Expected {order_time=} < {mock_current_time=}"


def test_exchange_time_future():
    # Given exchange timestamp
    exchange_timestamp = "2024-12-18 09:22:35"

    # Mock current time to ensure test consistency
    mock_current_time = pdlm.datetime(2024, 12, 18, 9, 22, 30, tz="Asia/Kolkata")

    # Parse the exchange timestamp into a Pendulum time object
    exchange_time = pdlm.parse(exchange_timestamp, strict=False, tz="Asia/Kolkata")

    # Validate that exchange time is correctly identified as in the future
    with patch("pendulum.now", return_value=mock_current_time):
        assert (
            exchange_time > mock_current_time
        ), f"Expected {exchange_time=} > {mock_current_time=}"


def test_exchange_time_past():
    # Given exchange timestamp
    exchange_timestamp = "2024-12-18 09:22:35"

    # Mock current time to ensure test consistency
    mock_current_time = pdlm.datetime(2024, 12, 18, 9, 22, 40, tz="Asia/Kolkata")

    # Parse the exchange timestamp into a Pendulum time object
    exchange_time = pdlm.parse(exchange_timestamp, strict=False, tz="Asia/Kolkata")

    # Validate that exchange time is correctly identified as in the past
    with patch("pendulum.now", return_value=mock_current_time):
        assert (
            exchange_time < mock_current_time
        ), f"Expected {exchange_time=} < {mock_current_time=}"


if __name__ == "__main__":
    try:
        test_order_time_future()
        print("test_order_time_future passed.")
        test_order_time_past()
        print("test_order_time_past passed.")
        test_exchange_time_future()
        print("test_exchange_time_future passed.")
        test_exchange_time_past()
        print("test_exchange_time_past passed.")
    except AssertionError as e:
        print(f"Test failed: {e}")
