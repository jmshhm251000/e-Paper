from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
from image import quantize_with_palette
import shutil
import os
import subprocess

# Paths
STATIC_DIR = "static"
UPLOAD_DIR = "pic"
EPAPER_SCRIPT = "/home/minseok/myepaper/test.py"

# Create folders if they don't exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/images")
def list_images():
    """List all PNG images in static/ folder"""
    return [f for f in os.listdir(STATIC_DIR) if f.lower().endswith(".png")]


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """Upload and process an image"""
    filename_base, _ = os.path.splitext(file.filename)
    raw_path = os.path.join(UPLOAD_DIR, file.filename)
    bmp_path = os.path.join(UPLOAD_DIR, f"{filename_base}.bmp")
    png_path = os.path.join(STATIC_DIR, f"{filename_base}.png")

    # Save uploaded file
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Process and save
    try:
        img = Image.open(raw_path)
        processed = quantize_with_palette(img)
        processed.save(bmp_path, format="BMP")
        processed.save(png_path, format="PNG")
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    # Clean up raw file
    os.remove(raw_path)

    return {
        "status": "success",
        "preview": f"/static/{filename_base}.png",
        "bmp_path": bmp_path,
    }


class FileNameRequest(BaseModel):
    file_name: str


@app.post("/display")
async def display_image(req: FileNameRequest):
    """Send selected BMP file to e-Paper"""
    bmp_path = os.path.join(UPLOAD_DIR, req.file_name)

    if not os.path.exists(bmp_path):
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    try:
        subprocess.run(["/usr/bin/python3", EPAPER_SCRIPT, bmp_path], check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    return {"status": "success", "file": req.file_name}
