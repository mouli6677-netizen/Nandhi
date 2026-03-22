# dashboard_api.py

from fastapi import FastAPI, WebSocket, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from core.engine_instance import engine
import shutil, os, asyncio

app = FastAPI()

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Nandhi Dashboard</title>
</head>
<body>
<h1>Nandhi Live Brain Dashboard</h1>

<div>
<h2>Memory & Stats</h2>
<div id="stats"></div>
</div>

<div>
<h2>Upload Image</h2>
<form id="imgForm" enctype="multipart/form-data">
<input type="file" name="file" id="fileInput"/>
<select id="operation">
  <option value="grayscale">Grayscale</option>
  <option value="blur">Blur</option>
</select>
<button type="button" onclick="uploadImage()">Upload & Edit</button>
</form>
<div id="imgResult"></div>
</div>

<div>
<h2>Upload Video</h2>
<form id="videoForm" enctype="multipart/form-data">
<input type="file" name="file" id="videoInput"/>
<button type="button" onclick="uploadVideo()">Upload & Analyze</button>
</form>
<div id="videoResult"></div>
</div>

<script>
let ws = new WebSocket("ws://localhost:8080/ws");
ws.onmessage = (event) => {
    document.getElementById("stats").innerText = event.data;
};

async function uploadImage(){
    let input = document.getElementById("fileInput");
    let operation = document.getElementById("operation").value;
    if(input.files.length == 0) return alert("Select a file");
    let file = input.files[0];
    let formData = new FormData();
    formData.append("file", file);
    formData.append("operation", operation);
    let res = await fetch("/upload_image", {method:"POST", body: formData});
    let text = await res.text();
    document.getElementById("imgResult").innerText = text;
}

async function uploadVideo(){
    let input = document.getElementById("videoInput");
    if(input.files.length == 0) return alert("Select a file");
    let file = input.files[0];
    let formData = new FormData();
    formData.append("file", file);
    let res = await fetch("/upload_video", {method:"POST", body: formData});
    let text = await res.text();
    document.getElementById("videoResult").innerText = text;
}
</script>
</body>
</html>
"""

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def get_dashboard():
    return HTMLResponse(HTML)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await asyncio.sleep(1)
        # FIX: original called engine.memory.search("", top_k=1000) but
        # PersistentMemory has no .search() method — it only has
        # load_recent_messages(). Use engine.memory_count() which is now
        # defined correctly on NandhiEngine.
        mem_count = engine.memory_count()
        await websocket.send_text(f"Memory Count: {mem_count}")


@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...), operation: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    output_path = os.path.join(UPLOAD_DIR, f"edited_{file.filename}")
    # FIX: engine.tools was never initialised on the original NandhiEngine,
    # so this call raised AttributeError. engine.tools is now a ToolRegistry
    # instance set up in __init__.
    result = engine.tools.edit_image(file_path, output_path, operation)
    return result


@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    frames_dir = os.path.join(UPLOAD_DIR, f"frames_{os.path.splitext(file.filename)[0]}")
    # FIX: same engine.tools AttributeError as above.
    result = engine.tools.extract_frames(file_path, frames_dir, step=30)
    return result