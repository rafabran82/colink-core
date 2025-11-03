import os, sys
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import WebsocketClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import safe_sign_and_autofill_transaction, send_reliable_submission

load_dotenv(".env.testnet")

ENDPOINT = os.getenv("XRPL_ENDPOINT","wss://s.altnet.rippletest.net:51233")
ISSUER_ADDR = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED"); HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE = os.getenv("COPX_CODE","COPX")
DRY = os.getenv("DRY_RUN","true").lower() == "true"

SEED_LP_COPX = Decimal(os.getenv("SEED_LP_COPX","500000"))
SEED_LP_COL  = Decimal(os.getenv("SEED_LP_COL","100000"))
SEED_LP_XRP  = Decimal(os.getenv("SEED_LP_XRP","2000"))

def iou(value, code, issuer):
    return {"currency": code, "issuer": issuer, "value": str(value)}

def main():
    if not all([HOT_SEED, HOT_ADDR, ISSUER_ADDR]):
        print("Fill .env.testnet secrets first."); sys.exit(1)

    w = Wallet(seed=HOT_SEED, sequence=0)

    with WebsocketClient(ENDPOINT) as client:
        offer1 = OfferCreate(
            account=HOT_ADDR,
            taker_pays=iou(SEED_LP_COPX, CODE, ISSUER_ADDR),
            taker_gets=str(int(SEED_LP_XRP * 1_000_000))  # XRP in drops
        )
        offer2 = OfferCreate(
            account=HOT_ADDR,
            taker_pays=iou(SEED_LP_COL, "COL", HOT_ADDR),
            taker_gets=iou(SEED_LP_COPX/5, CODE, ISSUER_ADDR)
        )

        for idx, off in enumerate([offer1, offer2], start=1):
            if DRY:
                print(f"[DRY] Offer {idx}:", off.to_dict())
            else:
                stx = safe_sign_and_autofill_transaction(off, w, client)
                resp = send_reliable_submission(stx, client)
                print(f"Offer {idx}:", resp.result)
    print("Done (offers).")

if __name__ == "__main__":
    main()
