import os, sys, json
from dotenv import load_dotenv
from xrpl.clients import WebsocketClient
from xrpl.models.requests import BookOffers

load_dotenv(".env.testnet")
ENDPOINT = os.getenv("XRPL_ENDPOINT","wss://s.altnet.rippletest.net:51233")
ISSUER_ADDR = os.getenv("XRPL_ISSUER_ADDRESS")
HOT_ADDR = os.getenv("XRPL_HOT_ADDRESS")
CODE = os.getenv("COPX_CODE","COPX")

def iou(code, issuer):
    return {"currency": code, "issuer": issuer}

def main():
    with WebsocketClient(ENDPOINT) as client:
        r1 = client.request(BookOffers(taker_gets=iou(CODE, ISSUER_ADDR), taker_pays="XRP")).result
        print("Orderbook COPX/XRP sample:")
        print(json.dumps(r1.get("offers", [])[:5], indent=2))

        r2 = client.request(BookOffers(taker_gets=iou("COL", HOT_ADDR), taker_pays=iou(CODE, ISSUER_ADDR))).result
        print("Orderbook COL/COPX sample:")
        print(json.dumps(r2.get("offers", [])[:5], indent=2))

if __name__ == "__main__":
    main()
