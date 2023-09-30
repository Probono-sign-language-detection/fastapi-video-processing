from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def close_all_connections(self):
        for connection in self.active_connections:
            await connection.close()
            self.active_connections.remove(connection)


websocket_manager = ConnectionManager()