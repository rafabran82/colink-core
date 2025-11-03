import os, json
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountOffers
from xrpl.models.transactions import OfferCancel
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")
RPC    = os.getenv("XRPL_RPC","https://s.altnet.rippletest.net:51234")
MAKER  = os.getenv("XRPL_MAKER_ADDRESS")
MSEED  = os.getenv("XRPL_MAKER_SEED")

def main():
    if not (MAKER and MSEED):
        print("Set XRPL_MAKER_ADDRESS and XRPL_MAKER_SEED")
        return
    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(MSEED)

    res = c.request(AccountOffers(account=MAKER, ledger_index="validated")).result
    offers = res.get("offers",[]) or []
    if not offers:
        print("No maker offers to cancel.")
        return

    results = []
    for o in offers:
        seq = o.get("seq") or o.get("Sequence")
        if not seq: continue
        tx = OfferCancel(account=MAKER, offer_sequence=seq)
        stx = sign(autofill(tx, c), w)
        r = submit_and_wait(stx, c).result
        results.append({"seq": seq, "engine_result": r.get("engine_result")})
    print(json.dumps({"cancelled": results}, indent=2))

if __name__ == "__main__":
    main()
