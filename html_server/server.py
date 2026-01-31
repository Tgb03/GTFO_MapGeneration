from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
import json

app = FastAPI()

SVG_DATA = {}
subscribers = set()

@app.get("/")
async def index():
    return HTMLResponse(open("index.html").read())

@app.get("/current_svg/{id}")
async def current_svg(id: str):
    return SVG_DATA.get(id, "")

@app.post("/svg/{id}")
async def update_svg(id: str, request: Request):
    svg = (await request.body()).decode("utf-8")
    SVG_DATA[id] = svg

    # Wrap SVG in JSON safely
    payload = json.dumps({"id": id, "svg": svg})

    for q in subscribers:
        await q.put(payload)

    return {"ok": True}



@app.get("/events")
async def events():
    async def event_generator():
        q = asyncio.Queue()
        subscribers.add(q)
        try:
            while True:
                data = await q.get()
                yield f"event: svg\ndata: {data}\n\n"
        finally:
            subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )