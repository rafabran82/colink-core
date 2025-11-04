from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/_echo")
async def echo(req: Request):
    body = await req.body()
    return {
        "method": req.method,
        "headers": {k: v for k, v in req.headers.items()
                    if k.lower().startswith("x-xrpay-") or k.lower()=="idempotency-key"},
        "raw": body.decode("utf-8", "replace")
    }
