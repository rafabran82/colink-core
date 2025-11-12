"""
xrpl_compat: normalize to call sites:
  safe_sign_and_autofill_transaction(tx, client, wallet)
  send_reliable_submission(signed_tx, client)
Implemented via xrpl.asyncio.transaction (works across xrpl-py versions).
"""
import asyncio
from xrpl.asyncio.transaction import (
    autofill as _autofill_async,
    safe_sign_and_autofill_transaction as _safe_sign_and_autofill_async,
    send_reliable_submission as _send_reliable_submission_async,
)

def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nest gracefully if already inside an event loop (rare for CLI)
            return asyncio.run(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No existing loop
        return asyncio.run(coro)

def safe_sign_and_autofill_transaction(tx, client, wallet):
    """
    Expected order: (tx, client, wallet).
    We delegate to the async helper which expects (tx, wallet, client).
    """
    return _run(_safe_sign_and_autofill_async(tx, wallet, client))

def send_reliable_submission(signed_tx, client):
    return _run(_send_reliable_submission_async(signed_tx, client))
