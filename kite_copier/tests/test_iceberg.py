
from time import sleep

freeze = {"symbol": "abc", "quantity": 850}
dct_ldr = {"symbol": "abc", "quantity": 900}
dct_flwr = {"symbol": "abc", "quantity": 50}
dct_lots = {"abc": 50}
max_lots = {"abc": 850}

print(f"ldr {dct_ldr}")

dct_multiplied = {k: (v*2.0125 if k == "quantity" else v)
                  for k, v in dct_ldr.items()}
print(f"after multiply {dct_multiplied}")

lot = dct_lots[dct_multiplied.get('symbol')]
dct_rnd = {"symbol": dct_multiplied.get(
    "symbol"), "quantity": int(dct_multiplied.get("quantity") / lot) * lot}

print(f" flwr: {dct_flwr}")
# Add corresponding integer values from dct_rnd and dct_flwr to form a new dictionary
resultant_dict = {}
for key in dct_rnd:
    if isinstance(dct_rnd[key], int) and isinstance(dct_flwr[key], int):
        resultant_dict[key] = dct_rnd[key] + dct_flwr[key]
    else:
        resultant_dict[key] = dct_rnd[key]
print(f" res {resultant_dict}")


ldr = [900]
flwr = [-50]
multiply = 2.0125
max = 850
lot = 50

while True:
    lst_mul = [q*multiply for q in ldr]
    print("multiplied", lst_mul)
    rnd = sum(int(q/lot)*lot for q in lst_mul)
    print("rounded", rnd)
    lst_rnd = []
    mod = rnd % max
    if mod > 0:
        print("mod", mod)
        lst_rnd = [mod]
        trgt = [sum(lst_rnd)-sum(flwr)]
        flwr = flwr.extend(trgt) if trgt == [0] else [0]
        print("flwr", flwr)
    for q in range(int(rnd/max)):
        lst_rnd = [lot]
        trgt = [sum(lst_rnd)-sum(flwr)]
        flwr = flwr.extend(trgt) if trgt == [0] else [0]
        print("flwr", flwr)
