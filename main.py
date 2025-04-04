
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil, os, uuid, datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(resume: UploadFile = File(...)):
    resume_id = str(uuid.uuid4())[:8]
    input_path = f"temp/{resume_id}_input.pdf"
    output_path = f"temp/{resume_id}_tracked.pdf"
    pixel_url = "static/transparent.gif"

    with open(input_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(600, 800))
    c.drawImage(pixel_url, 1, 1, width=1, height=1)
    c.save()
    buffer.seek(0)

    base = PdfReader(input_path)
    pixel_page = PdfReader(buffer)
    writer = PdfWriter()

    for page in base.pages:
        writer.add_page(page)
    writer.add_page(pixel_page.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)

    return FileResponse(output_path, filename="tracked_resume.pdf")

@app.get("/pixel")
async def pixel(request: Request):
    resume_id = request.query_params.get("id", "unknown")
    ip = request.client.host
    ua = request.headers.get("user-agent", "unknown")
    timestamp = datetime.datetime.utcnow().isoformat()

    os.makedirs("logs", exist_ok=True)
    with open("logs/tracking_log.csv", "a") as log:
        log.write(f"{resume_id},{timestamp},{ip},{ua}\n")

    return FileResponse("static/transparent.gif", media_type="image/gif")
