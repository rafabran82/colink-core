from xrpl.clients import JsonRpcClient
from xrpl.transaction import autofill, sign, reliable_submission

def safe_sign_and_autofill_transaction(tx, wallet, client):
    # Ensure client has network_id for newer SDKs
    if not hasattr(client, "network_id"):
        client.network_id = None

    # Fully synchronous: autofill → sign
    tx = autofill(tx, client)
    signed = sign(tx, wallet)
    return signed


def send_reliable_submission(signed_tx, client):
    # Wrapper for renamed reliable_submission()
    return reliable_submission(signed_tx, client)
