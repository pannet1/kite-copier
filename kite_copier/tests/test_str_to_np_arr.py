import numpy as np


def string_to_numpy_array(input_string):
    """
    Converts a string formatted like a NumPy array into a NumPy array.

    Args:
        input_string (str): A string in the format "[value1 value2 ...]".

    Returns:
        np.ndarray: A NumPy array of floats.
    """
    try:
        # Strip the brackets and split by whitespace
        values = input_string.strip("[]").split()
        return np.array([float(value) for value in values])
    except ValueError as e:
        raise ValueError(
            f"Invalid input string for conversion: {input_string}. Error: {e}"
        )


# Example Usage
example_string = "[130.995  152.8275 160.105  167.3825 174.66   181.9375 189.215 ]"
result_array = string_to_numpy_array(example_string)
print(
    result_array
)  # Output: [130.995  152.8275 160.105  167.3825 174.66   181.9375 189.215 ]


def test_string_to_numpy_array():
    input_string = "[130.995  152.8275 160.105  167.3825 174.66   181.9375 189.215 ]"
    expected_output = np.array(
        [130.995, 152.8275, 160.105, 167.3825, 174.66, 181.9375, 189.215]
    )
    result = string_to_numpy_array(input_string)
    np.testing.assert_array_almost_equal(result, expected_output, decimal=6)


# Run the test
if __name__ == "__main__":
    test_string_to_numpy_array()
    print("Test passed!")
