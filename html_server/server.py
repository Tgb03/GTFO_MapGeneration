from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
import json

app = FastAPI()

SVG_DATA = {}
clients = set()


@app.get("/")
async def index():
    return HTMLResponse(open("index.html").read())

@app.get("/current_svg/{id}")
async def current_svg(id: str):
    return PlainTextResponse(SVG_DATA.get(id, ""))

@app.post("/svg/{id}")
async def update_svg(id: str, request: Request):
    svg = (await request.body()).decode("utf-8")
    SVG_DATA[id] = svg

    # Wrap SVG in JSON safely
    payload = json.dumps({"id": id, "svg": svg})

    for ws in clients:
        await ws.send_text(payload)

    return {"ok": True}



@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        clients.remove(ws)