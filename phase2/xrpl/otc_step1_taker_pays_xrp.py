import os, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")
RPC      = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
TAKER    = os.getenv("XRPL_TAKER_ADDRESS")
TAKER_SD = os.getenv("XRPL_TAKER_SEED")
MAKER    = os.getenv("XRPL_MAKER_ADDRESS")

# Amount of XRP the taker pays (drops). Use the same cap you used for the IOC: ~1.020020 drops.
XRP_DROPS = int(os.getenv("OTC_XRP_DROPS","1020020"))

def main():
    if not all([TAKER,TAKER_SD,MAKER]):
        print("Missing TAKER/MAKER envs")
        return
    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(TAKER_SD)

    pay = Payment(
        account=TAKER,
        destination=MAKER,
        amount=str(XRP_DROPS)  # drops
    )
    stx = sign(autofill(pay, c), w)
    res = submit_and_wait(stx, c).result
    print(json.dumps({
        "engine_result": res.get("engine_result"),
        "hash": res.get("tx_json",{}).get("hash"),
        "xrp_drops_sent": XRP_DROPS
    }, indent=2))

if __name__ == "__main__":
    main()
