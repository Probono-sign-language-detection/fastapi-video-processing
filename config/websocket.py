from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from fastapi.responses import HTMLResponse
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    @staticmethod
    def is_socket_connected(websocket: WebSocket) -> bool:
        return websocket.client_state == WebSocketState.CONNECTED and websocket.application_state == WebSocketState.CONNECTED

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        existing_socket = self.active_connections.get(client_id)
        try:
            if existing_socket and self.is_socket_connected(existing_socket):
                await existing_socket.close()
        except Exception as e:
            print(f"Error closing WebSocket: {e}")
            
        self.active_connections[client_id] = websocket

    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

websocket_manager = ConnectionManager()