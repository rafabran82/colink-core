import asyncio
from typing import Sequence

try:
    from xrpl.asyncio.clients import AsyncWebsocketClient
    from xrpl.models.requests import Subscribe
except Exception:
    AsyncWebsocketClient = None
    Subscribe = None

class XRPLWatcher:
    def __init__(self, ws_url: str, accounts: Sequence[str], outbox_repo):
        self.ws_url = ws_url
        self.accounts = list(accounts)
        self.outbox_repo = outbox_repo

    async def run(self):
        if AsyncWebsocketClient is None:
            # xrpl-py not installed; mock mode
            while True:
                await asyncio.sleep(1.0)
        else:
            async with AsyncWebsocketClient(self.ws_url) as client:
                sub = Subscribe(streams=["transactions"], accounts=self.accounts)
                await client.send(sub)
                async for msg in client:
                    tx = msg.get("transaction")
                    if not tx or tx.get("TransactionType") != "Payment":
                        continue
                    if tx.get("Destination") not in self.accounts:
                        continue
                    ev = self._to_ledger_event(tx)
                    await self.outbox_repo.enqueue("invoice.payment_detected", ev)

    def _to_ledger_event(self, tx: dict) -> dict:
        return {
            "tx_hash": tx.get("hash"),
            "amount": tx.get("Amount"),
            "destination": tx.get("Destination"),
            "destination_tag": tx.get("DestinationTag"),
            "invoice_id": tx.get("DestinationTag"),  # simple mapping for now
            "status": "DETECTED"
        }

