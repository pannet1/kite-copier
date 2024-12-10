import pendulum as pdlm


order_timestamp = "11:37:02"

# Current time with an added second
current_time = pdlm.now("Asia/Kolkata").add(seconds=1)

# Parse the order timestamp into a pdlm time object
# Assuming the order timestamp is for today's date
order_time = pdlm.parse(order_timestamp, strict=False, tz="Asia/Kolkata")

# Add today's date to the order time for an accurate comparison
"""

order_time = order_time.replace(
    year=current_time.year, month=current_time.month, day=current_time.day
)
    """

try:
    while True:
        if order_time > current_time:
            print(f"The {order_time=} > {current_time} is in the future.")
        else:
            print(f"The {order_time=} is in the past.")
        __import__("time").sleep(1)
except KeyboardInterrupt:
    __import__("sys").exit()
