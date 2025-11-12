"""
xrpl_compat: small compatibility layer so our call sites consistently use
  safe_sign_and_autofill_transaction(tx, client, wallet)
  send_reliable_submission(tx_signed, client)
across xrpl-py versions.
"""
from xrpl.transaction import (
    autofill as _autofill,
    safe_sign_and_autofill_transaction as _safe_sign_and_autofill,
    send_reliable_submission as _send_reliable_submission,
)

def safe_sign_and_autofill_transaction(tx, client, wallet):
    """
    Normalize call order: (tx, client, wallet).
    Steps:
      1) autofill with client
      2) safe_sign_and_autofill with wallet + client
    """
    tx = _autofill(tx, client)
    signed = _safe_sign_and_autofill(tx, wallet, client)
    return signed

def send_reliable_submission(signed_tx, client):
    return _send_reliable_submission(signed_tx, client)
