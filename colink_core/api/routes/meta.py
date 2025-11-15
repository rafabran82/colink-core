from fastapi import APIRouter

router = APIRouter()

@router.get("/meta")
async def get_meta():
    return {
        "status": "ok",
        "engine": "demo",
        "timestamp": "2025-01-01T00:00:00Z"
    }
