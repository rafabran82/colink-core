from __future__ import annotations

from fastapi import HTTPException


def http500(e: Exception, detail: str | dict | None = None) -> Exception:
    if detail is None:
        detail = str(e)
    # attach original exception for logs, but keep clean client detail
    return HTTPException(status_code=500, detail=detail)


def http400(e: Exception, detail: str | dict | None = None) -> Exception:
    if detail is None:
        detail = str(e)
    return HTTPException(status_code=400, detail=detail)

