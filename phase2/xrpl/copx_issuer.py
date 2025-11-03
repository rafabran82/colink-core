import os, sys, json
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import WebsocketClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment, TrustSet
from xrpl.transaction import safe_sign_and_autofill_transaction, send_reliable_submission

load_dotenv(".env.testnet")

ENDPOINT = os.getenv("XRPL_ENDPOINT","wss://s.altnet.rippletest.net:51233")
ISSUER_SEED = os.getenv("XRPL_ISSUER_SEED")
ISSUER_ADDR = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED")
HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE = os.getenv("COPX_CODE","COPX")
DRY = os.getenv("DRY_RUN","true").lower() == "true"
ISSUANCE = Decimal(os.getenv("ISSUANCE_AMOUNT","1000000"))

def issued_currency(amount, currency, issuer):
    return {"currency": currency, "issuer": issuer, "value": str(amount)}

def main():
    if not all([ISSUER_SEED, ISSUER_ADDR, HOT_SEED, HOT_ADDR]):
        print("Missing keys in .env.testnet. Fill testnet secrets first."); sys.exit(1)

    issuer = Wallet(seed=ISSUER_SEED, sequence=0)
    hot = Wallet(seed=HOT_SEED, sequence=0)

    with WebsocketClient(ENDPOINT) as client:
        trust = TrustSet(
            account=HOT_ADDR,
            limit_amount=issued_currency(ISSUANCE, CODE, ISSUER_ADDR),
        )
        if DRY:
            print("[DRY] TrustSet:", trust.to_dict())
        else:
            stx = safe_sign_and_autofill_transaction(trust, hot, client)
            resp = send_reliable_submission(stx, client)
            print("TrustSet:", resp.result)

        pay = Payment(
            account=ISSUER_ADDR,
            destination=HOT_ADDR,
            amount=issued_currency(ISSUANCE, CODE, ISSUER_ADDR),
        )
        if DRY:
            print("[DRY] Issue Payment:", pay.to_dict())
        else:
            stx = safe_sign_and_autofill_transaction(pay, issuer, client)
            resp = send_reliable_submission(stx, client)
            print("Issuance:", resp.result)

    print("Done (issuer/trust).")

if __name__ == "__main__":
    main()
