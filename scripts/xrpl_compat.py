"""
xrpl_compat: normalize call sites to:
  safe_sign_and_autofill_transaction(tx, client, wallet)
  send_reliable_submission(signed_tx, client)

Works across xrpl-py versions by importing what's available and falling back.
"""
import asyncio

# Try sync imports first
_safe_sync = None
_sign_sync = None
_autofill_sync = None
_send_sync = None

try:
    from xrpl.transaction import (
        autofill as _autofill_sync,
        send_reliable_submission as _send_sync,
        safe_sign_and_autofill_transaction as _safe_sync,
    )
except Exception:
    # older/newer variants may not export _safe_sync
    try:
        from xrpl.transaction import (
            autofill as _autofill_sync,
            send_reliable_submission as _send_sync,
        )
    except Exception:
        pass

# Try to get sync sign()
if _sign_sync is None:
    try:
        from xrpl.transaction import sign as _sign_sync
    except Exception:
        _sign_sync = None

# Async fallbacks
_sign_async = None
_send_async = None
_autofill_async = None
try:
    from xrpl.asyncio.transaction import (
        sign as _sign_async,
        send_reliable_submission as _send_async,
        autofill as _autofill_async,
    )
except Exception:
    pass

def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

def safe_sign_and_autofill_transaction(tx, client, wallet):
    """
    Expected order: (tx, client, wallet). Internally:
      - prefer native safe_sign_and_autofill_transaction(tx, wallet, client)
      - else: autofill(tx, client), then sign(tx, wallet)
    Returns a SignedTransaction (as provided by xrpl-py).
    """
    # 1) Native sync helper available?
    if _safe_sync is not None:
        return _safe_sync(tx, wallet, client)

    # 2) Autofill (sync preferred)
    if _autofill_sync is not None:
        tx = _autofill_sync(tx, client)
    elif _autofill_async is not None:
        tx = _run(_autofill_async(tx, client))
    else:
        raise RuntimeError("xrpl_compat: no autofill available (sync or async).")

    # 3) Sign (sync preferred)
    if _sign_sync is not None:
        signed = _sign_sync(tx, wallet)
    elif _sign_async is not None:
        signed = _run(_sign_async(tx, wallet))
    else:
        raise RuntimeError("xrpl_compat: no sign() available (sync or async).")

    return signed

def send_reliable_submission(signed_tx, client):
    # prefer sync
    if _send_sync is not None:
        return _send_sync(signed_tx, client)
    if _send_async is not None:
        return _run(_send_async(signed_tx, client))
    raise RuntimeError("xrpl_compat: no send_reliable_submission available.")
