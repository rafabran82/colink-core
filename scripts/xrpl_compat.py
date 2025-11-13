import json
from xrpl.clients import JsonRpcClient
from xrpl.transaction import sign
from xrpl.core import addresscodec
from xrpl.models.transactions import Transaction
import xrpl.asyncio.transaction.main as async_tx


def _autofill_sync(tx: Transaction, client: JsonRpcClient):
    # Patch: ensure client has network_id for new SDKs
    if not hasattr(client, "network_id"):
        client.network_id = None

    # Use raw autofill logic but with our patched client
    return async_tx.autofill(tx, client)


def safe_sign_and_autofill_transaction(tx, wallet, client):
    # Patch: ensure client has network_id
    if not hasattr(client, "network_id"):
        client.network_id = None

    # Autofill
    tx = _autofill_sync(tx, client)

    # Sync sign
    signed = sign(tx, wallet)
    return signed


def send_reliable_submission(signed, client):
    # Simple submit wrapper (reliable submit from xrpl-py)
    from xrpl.transaction import send_reliable_submission as _send
    return _send(signed, client)
