import os, sys
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo
from xrpl.transaction import autofill, sign, submit_and_wait

load_dotenv(".env.testnet")

RPC = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(RPC)

ENDPOINT = os.getenv("XRPL_ENDPOINT","wss://s.altnet.rippletest.net:51233")
ISSUER_SEED = os.getenv("XRPL_ISSUER_SEED")
ISSUER_ADDR = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_SEED = os.getenv("XRPL_HOT_SEED")
HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE = os.getenv("COPX_CODE","COPX")
DRY = os.getenv("DRY_RUN","true").lower() == "true"
ISSUANCE = Decimal(os.getenv("ISSUANCE_AMOUNT","1000000"))

def iou_amt(value, code, issuer):
    return IssuedCurrencyAmount(currency=code, issuer=issuer, value=str(Decimal(value)))

def main():
    if not all([ISSUER_SEED, ISSUER_ADDR, HOT_SEED, HOT_ADDR]):
        print("Missing keys in .env.testnet."); sys.exit(1)

    issuer = Wallet(seed=ISSUER_SEED, sequence=0)
    hot = Wallet(seed=HOT_SEED, sequence=0)

    # 1) Hot wallet adds trustline to COPX issued by ISSUER
    trust = TrustSet(
        account=HOT_ADDR,
        limit_amount=iou_amt(ISSUANCE, CODE, ISSUER_ADDR),
    )

    # 2) Issuer sends COPX IOUs to hot wallet
    pay = Payment(
        account=ISSUER_ADDR,
        destination=HOT_ADDR,
        amount=iou_amt(ISSUANCE, CODE, ISSUER_ADDR)
    )

    if DRY:
        print("[DRY] TrustSet:", trust.to_xrpl())
        print("[DRY] Payment :", pay.to_xrpl())
        return

    # Live submit with 2.x helpers
    trust_filled = autofill(trust, client)
    trust_signed = sign(trust_filled, hot)
    trust_result = submit_and_wait(trust_signed, client)
    print("TrustSet result:", trust_result.result)

    pay_filled = autofill(pay, client)
    pay_signed = sign(pay_filled, issuer)
    pay_result = submit_and_wait(pay_signed, client)
    print("Issuance result:", pay_result.result)

    print("Done.")
if __name__ == "__main__":
    main()
