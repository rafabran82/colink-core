import os, sys
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.utils import xrp_to_drops

load_dotenv(".env.testnet")

RPC = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)

ISSUER_ADDR = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED"); HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE = os.getenv("COPX_CODE","COPX")
DRY = os.getenv("DRY_RUN","true").lower() == "true"

SEED_LP_COPX = Decimal(os.getenv("SEED_LP_COPX","500000"))
SEED_LP_COL  = Decimal(os.getenv("SEED_LP_COL","100000"))
SEED_LP_XRP  = Decimal(os.getenv("SEED_LP_XRP","2000"))

def iou_amt(value, code, issuer):
    return IssuedCurrencyAmount(currency=code, issuer=issuer, value=str(Decimal(value)))

def main():
    if not all([HOT_SEED, HOT_ADDR, ISSUER_ADDR]):
        print("Fill .env.testnet secrets first."); sys.exit(1)

    w = Wallet(seed=HOT_SEED, sequence=0)

    # Offer 1: pay COPX, get XRP (sell COPX for XRP)
    offer1 = OfferCreate(
        account=HOT_ADDR,
        taker_pays=iou_amt(SEED_LP_COPX, CODE, ISSUER_ADDR),
        taker_gets=xrp_to_drops(SEED_LP_XRP)  # drops string
    )
    # Offer 2: pay COL (demo IOU from HOT), get COPX
    offer2 = OfferCreate(
        account=HOT_ADDR,
        taker_pays=iou_amt(SEED_LP_COL, "COL", HOT_ADDR),
        taker_gets=iou_amt(SEED_LP_COPX/5, CODE, ISSUER_ADDR)
    )

    if DRY:
        print("[DRY] Offer 1:", offer1.to_xrpl())
        print("[DRY] Offer 2:", offer2.to_xrpl())
        return

    for idx, off in enumerate([offer1, offer2], start=1):
        filled = autofill(off, client)
        signed = sign(filled, w)
        resp = submit_and_wait(signed, client)
        print(f"Offer {idx} result:", resp.result)

    print("Done.")
if __name__ == "__main__":
    main()
