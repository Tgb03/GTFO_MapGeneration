from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse
import json

app = FastAPI()

FRAME_DATA = {}  # id -> last payload (svg or error)
clients = set()


@app.get("/")
async def index():
    return HTMLResponse(open("index.html").read())

@app.get("/current_frame/{id}")
async def current_frame(id: str):
    return PlainTextResponse(json.dumps(FRAME_DATA.get(id, {"svg": ""})))

@app.post("/svg/{id}")
async def update_svg(id: str, request: Request):
    raw = (await request.body()).decode("utf-8")
    try:
        body = json.loads(raw)
        # Expect either {"svg": "<svg...>"} or {"error": "some message"}
    except json.JSONDecodeError:
        # Legacy: raw SVG string posted directly
        body = {"svg": raw}
    FRAME_DATA[id] = body

    payload = json.dumps({"id": id, **body})
    for ws in clients:
        await ws.send_text(payload)

    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        clients.remove(ws)