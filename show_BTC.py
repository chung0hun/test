import pickle

with open("BTC.bin", "rb") as f:
    BTC = pickle.load(f)

for n in range(24):
    print(f'{n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')