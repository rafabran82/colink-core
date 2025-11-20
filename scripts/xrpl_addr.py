import sys
from xrpl.wallet import Wallet

if len(sys.argv) != 2:
    print("ERR")
    sys.exit(1)

seed = sys.argv[1]

try:
    w = Wallet(seed, 0)
    print(w.classic_address)
except Exception as e:
    print("ERR")
    sys.exit(1)
