import os, json, time
from decimal import Decimal
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import Tx
from xrpl.transaction import autofill, sign, submit_and_wait

def env(name, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env: {name}")
    return v

def to160(code:str)->str:
    if len(code)<=3: return code
    b=code.encode("ascii")
    if len(b)>20: raise ValueError("currency code >20 bytes")
    return b.hex().upper().ljust(40,"0")

def lookup_tx_outcome(client: JsonRpcClient, tx_hash: str, retries: int = 10, delay_s: float = 0.5):
    for _ in range(retries):
        r = client.request(Tx(transaction=tx_hash, binary=False)).result
        meta = r.get("meta") or {}
        tr = meta.get("TransactionResult")
        fee = r.get("Fee") or (r.get("tx") or {}).get("Fee") or "0"
        validated = bool(r.get("validated"))
        if tr:
            try:
                fee_i = int(fee)
            except Exception:
                fee_i = 0
            return tr, fee_i, validated
        time.sleep(delay_s)
    return None, 0, False

def main():
    load_dotenv(".env.testnet")
    RPC    = env("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    ISSUER = env("XRPL_ISSUER_ADDRESS", required=True)
    ISEED  = env("XRPL_ISSUER_SEED", required=True)
    TAKER  = env("XRPL_TAKER_ADDRESS", required=True)
    CODE   = to160(env("COPX_CODE", "COPX"))
    QTY    = Decimal(env("OTC_COPX_QTY", required=True))

    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(ISEED)

    out = {
        "engine_result": None,
        "hash": None,
        "fee_drops": 0,
        "issuer_sent": str(QTY),
    }

    try:
        amt = IssuedCurrencyAmount(currency=CODE, issuer=ISSUER, value=str(QTY))
        pay = Payment(account=ISSUER, destination=TAKER, amount=amt)
        stx = sign(autofill(pay, c), w)
        res = submit_and_wait(stx, c).result
        txj = res.get("tx_json") or {}
        h = txj.get("hash") or res.get("hash")
        out["hash"] = h

        eng = res.get("engine_result")
        if not eng and h:
            eng, fee, _ = lookup_tx_outcome(c, h)
            out["engine_result"] = eng
            out["fee_drops"] = fee
        else:
            out["engine_result"] = eng
            try:
                out["fee_drops"] = int(txj.get("Fee")) if str(txj.get("Fee","")).isdigit() else 0
            except Exception:
                pass
    except Exception as e:
        out["error"] = str(e)

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
