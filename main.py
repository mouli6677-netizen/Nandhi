# main.py
import os
import shutil
import asyncio
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from core.engine_instance import engine

app = FastAPI()
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")
UPLOAD_FOLDER = "media/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
async def index():
    with open("dashboard/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        try:
            data = await ws.receive_text()
            import json
            msg = json.loads(data)
            if msg["type"] == "chat":
                response = await engine.chat(msg["message"])
                stats = engine.get_stats()
                await ws.send_text(json.dumps({"type": "chat", "user": msg["message"], "response": response}))
                await ws.send_text(json.dumps({"type": "stats", "stats": stats}))
        except Exception as e:
            print(e)
            break

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = await engine.ingest_media(file_path)
    stats = engine.get_stats()
    return {"filename": file.filename, "result": result, "stats": stats}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)