# mypy: ignore-errors

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Supports segregating connections by channel (resource ID).
    """

    def __init__(self):
        # Map channel_id -> List[WebSocket]
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)

    def disconnect(self, websocket: WebSocket, channel_id: str):
        if channel_id in self.active_connections:
            if websocket in self.active_connections[channel_id]:
                self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]

    async def broadcast(self, message: str, channel_id: str):
        """Broadcast message to all connections in a specific channel."""
        if channel_id in self.active_connections:
            # Iterate over a copy to avoid modification during iteration issues if disconnect happens
            for connection in self.active_connections[channel_id][:]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Handle potential disconnection errors during broadcast
                    # In a robust system, we might remove the connection here
                    pass

    async def broadcast_json(self, data: dict, channel_id: str):
        """Broadcast JSON data to all connections in a specific channel."""
        if channel_id in self.active_connections:
            for connection in self.active_connections[channel_id][:]:
                try:
                    await connection.send_json(data)
                except Exception:
                    pass


manager = ConnectionManager()
