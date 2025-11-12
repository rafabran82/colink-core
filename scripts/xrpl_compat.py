# xrpl_compat.py — local shim to normalize xrpl-py API differences
from typing import Any
try:
    from xrpl.transaction import autofill, sign  # stable across versions
except Exception as e:  # pragma: no cover
    raise ImportError("xrpl.transaction.autofill/sign not found") from e

# send_reliable_submission may be submit_and_wait in some versions
try:
    from xrpl.transaction import send_reliable_submission  # type: ignore
except Exception:
    try:
        from xrpl.transaction import submit_and_wait as send_reliable_submission  # type: ignore
    except Exception as e:  # pragma: no cover
        def send_reliable_submission(*_a: Any, **_k: Any) -> Any:  # type: ignore
            raise RuntimeError("Neither send_reliable_submission nor submit_and_wait exists in this xrpl-py") from e

def safe_sign_and_autofill_transaction(tx: Any, wallet: Any, client: Any) -> Any:
    """Fallback implementation for older xrpl-py without the helper."""
    tx = autofill(tx, client)
    return sign(tx, wallet)
