from collections import defaultdict
import cv2
import numpy as np
from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import io
import asyncio
import tempfile
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Load YOLO model
model = YOLO(r"runs\detect\train23\weights\best.pt")
screen_res = (1920, 1080)
max_width, max_height = screen_res
track_history = defaultdict(lambda: [])

def scale_frame(frame, max_width, max_height):
    height, width = frame.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    return cv2.resize(frame, (new_width, new_height))

async def process_video(video_data: bytes = None, is_test: bool = False):
    if is_test:
        video_path = r"dataset\test.MOV"
        cap = cv2.VideoCapture(video_path)
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_data)
            tmp_file_path = tmp_file.name
        cap = cv2.VideoCapture(tmp_file_path)

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            result = model.track(frame, persist=True, conf=0.7, iou=0.4)[0]

            if result.boxes and result.boxes.is_track:
                boxes = result.boxes.xywh.cpu()
                track_ids = result.boxes.id.int().cpu().tolist()
                frame = result.plot()

                for box, track_id in zip(boxes, track_ids):
                    x, y, w, h = box
                    track = track_history[track_id]
                    track.append((float(x), float(y)))
                    if len(track) > 100:
                        track.pop(0)
                    points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

            frame_resized = scale_frame(frame, max_width, max_height)
            _, buffer = cv2.imencode('.jpg', frame_resized)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            await asyncio.sleep(1.0 / 24)  # 24 FPS

    finally:
        cap.release()
        if not is_test:
            os.unlink(tmp_file_path)

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "show_upload": True})

@app.get("/processing")
async def get_processing_screen(request: Request):
    return templates.TemplateResponse("components/video_processing.html", {"request": request})

@app.get("/process-test-video")
async def process_test_video():
    return StreamingResponse(process_video(is_test=True), media_type="multipart/x-mixed-replace;boundary=frame")

@app.post("/upload-video")
async def process_uploaded_video(file: UploadFile = File(...)):
    video_data = await file.read()
    return StreamingResponse(process_video(video_data), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)