import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from typing import Dict, Set

app = FastAPI(title="ChatCall")

connected_users: Dict[str, WebSocket] = {}
online_users: Set[str] = set()


@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open("templates/main.py.html", "r", encoding="utf-8") as f:
        return f.read()


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connected_users[username] = websocket
    online_users.add(username)
    await broadcast_online()
    try:
        while True:
            data = await websocket.receive_json()
            to_user = data.get("to")
            if data.get("type") == "chat" and to_user in connected_users:
                await connected_users[to_user].send_json({
                    "type": "chat",
                    "from": username,
                    "message": data.get("message")
                })
            elif data.get("type") in ["offer", "answer", "ice-candidate", "decline",
                                      "screen-stop"] and to_user in connected_users:
                data["from"] = username
                await connected_users[to_user].send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        connected_users.pop(username, None)
        online_users.discard(username)
        await broadcast_online()


async def broadcast_online():
    online_list = list(online_users)
    for username, ws in list(connected_users.items()):
        try:
            await ws.send_json({"type": "online", "users": online_list})
        except:
            connected_users.pop(username, None)
            online_users.discard(username)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render задаёт PORT автоматически
    uvicorn.run(app, host="0.0.0.0", port=port)  # убрал reload=True
