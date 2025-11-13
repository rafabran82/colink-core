from xrpl.clients import JsonRpcClient
from xrpl.transaction import autofill, sign, send_reliable_submission

def safe_sign_and_autofill_transaction(tx, wallet, client):
    # Ensure compatibility with newer SDKs expecting network_id
    if not hasattr(client, "network_id"):
        client.network_id = None

    # Fully synchronous autofill
    tx = autofill(tx, client)

    # Sign synchronously
    signed = sign(tx, wallet)
    return signed


def send_reliable_submission_sync(signed_tx, client):
    return send_reliable_submission(signed_tx, client)
