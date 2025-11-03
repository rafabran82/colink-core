import os, json, time
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient, WebsocketClient
from xrpl.models.requests import BookOffers
from xrpl.models.currencies import IssuedCurrency, XRP

load_dotenv(".env.testnet")
RPC = "https://s.altnet.rippletest.net:51234"
WSS = os.getenv("XRPL_ENDPOINT","wss://s.altnet.rippletest.net:51233")
ISSUER = os.getenv("XRPL_ISSUER_ADDRESS")
HOT    = os.getenv("XRPL_HOT_ADDRESS")
CODE   = os.getenv("COPX_CODE","COPX")

def to_160bit_hex(code: str) -> str:
    if len(code) <= 3:
        return code
    b = code.encode("ascii")
    if len(b) > 20:
        raise ValueError("Currency code >20 bytes not allowed")
    return b.hex().upper().ljust(40, "0")

CUR = to_160bit_hex(CODE)

def show(name, offers):
    print(name)
    print(json.dumps(offers[:5], indent=2))
    print()

def main():
    client = JsonRpcClient(RPC)

    # Give ledger a moment post-submit
    time.sleep(2)

    # JSON-RPC queries
    r1 = client.request(BookOffers(
        taker_gets=IssuedCurrency(currency=CUR, issuer=ISSUER),  # taker gets COPX
        taker_pays=XRP()
    )).result
    show("JSON-RPC: COPX/XRP (taker_gets COPX, pays XRP):", r1.get("offers", []))

    r2 = client.request(BookOffers(
        taker_gets=XRP(),                                         # taker gets XRP
        taker_pays=IssuedCurrency(currency=CUR, issuer=ISSUER)    # taker pays COPX
    )).result
    show("JSON-RPC: XRP/COPX (taker_gets XRP, pays COPX):", r2.get("offers", []))

    # WebSocket queries (same two views)
    with WebsocketClient(WSS) as ws:
        w1 = ws.request(BookOffers(
            taker_gets=IssuedCurrency(currency=CUR, issuer=ISSUER),
            taker_pays=XRP()
        )).result
        show("WS: COPX/XRP (taker_gets COPX, pays XRP):", w1.get("offers", []))

        w2 = ws.request(BookOffers(
            taker_gets=XRP(),
            taker_pays=IssuedCurrency(currency=CUR, issuer=ISSUER)
        )).result
        show("WS: XRP/COPX (taker_gets XRP, pays COPX):", w2.get("offers", []))

if __name__ == "__main__":
    main()
