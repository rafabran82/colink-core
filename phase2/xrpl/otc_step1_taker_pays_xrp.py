import os, json
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
DROPS    = int(os.getenv("OTC_XRP_DROPS","0"))

def main():
    if not (TAKER and TAKER_SD and MAKER and DROPS>0):
        print(json.dumps({"error":"missing env XRPL_TAKER_*, XRPL_MAKER_ADDRESS or OTC_XRP_DROPS"}, indent=2))
        return

    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(TAKER_SD)
    pay = Payment(account=TAKER, destination=MAKER, amount=str(DROPS))
    stx = sign(autofill(pay, c), w)
    res = submit_and_wait(stx, c).result

    out = {
        "engine_result": res.get("engine_result"),
        "validated": res.get("validated", False),
        "ledger_index": res.get("ledger_index"),
        "hash": (res.get("tx_json") or {}).get("hash"),
        "xrp_drops_sent": DROPS
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
