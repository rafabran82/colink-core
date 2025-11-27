import xrpl
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient

print("VERSION OK =", xrpl.__version__)
print("Client OK  =", JsonRpcClient)
print("Wallet OK  =", Wallet)
