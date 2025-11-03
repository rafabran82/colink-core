import os, json, time
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.models.requests import Tx
from xrpl.transaction import autofill, sign, submit_and_wait

def env(name, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env: {name}")
    return v

def lookup_tx_outcome(client: JsonRpcClient, tx_hash: str, retries: int = 10, delay_s: float = 0.5):
    """
    Resolve final outcome via Tx. Returns (engine_result, fee_drops, validated_bool).
    """
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
    RPC   = env("XRPL_RPC", "https://s.altnet.rippletest.net:51234")
    TAKER = env("XRPL_TAKER_ADDRESS", required=True)
    TSD   = env("XRPL_TAKER_SEED", required=True)
    MAKER = env("XRPL_MAKER_ADDRESS", required=True)
    drops_str = env("OTC_XRP_DROPS", required=True)

    try:
        drops = int(drops_str)
        if drops <= 0: raise ValueError()
    except Exception:
        raise RuntimeError(f"OTC_XRP_DROPS must be positive integer drops; got {drops_str!r}")

    c = JsonRpcClient(RPC)
    w = Wallet.from_seed(TSD)

    out = {
        "engine_result": None,
        "hash": None,
        "fee_drops": 0,
        "xrp_drops_sent": drops,
    }

    try:
        pay = Payment(account=TAKER, destination=MAKER, amount=str(drops))
        stx = sign(autofill(pay, c), w)
        res = submit_and_wait(stx, c).result
        txj = res.get("tx_json") or {}
        h = txj.get("hash") or res.get("hash")
        out["hash"] = h
        # Fallback resolve when engine_result is missing:
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
