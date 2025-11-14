from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Echo server for now — frontend expects a heartbeat
            msg = await websocket.receive_text()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass
