"""SalesBanana Web UI — thin FastAPI wrapper around generate_diagram()."""

import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import IMAGE_MODELS, settings
from src.pipeline import generate_diagram
from src.postprocessing import SLIDE_FORMATS

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="SalesBanana")

# Serve generated images from output directory
settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/slide-formats")
async def api_slide_formats():
    """Return available slide format presets for the UI dropdown."""
    return SLIDE_FORMATS


@app.get("/api/image-models")
async def api_image_models():
    """Return available image generation models for the UI dropdown."""
    return IMAGE_MODELS


@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    brief = body.get("brief", "").strip()
    slide_format = body.get("slide_format", "original")
    image_model = body.get("image_model")

    if not brief:
        return JSONResponse({"error": "Brief is required."}, status_code=400)

    if image_model and image_model not in IMAGE_MODELS:
        return JSONResponse({"error": f"Unknown image model: {image_model}"}, status_code=400)

    try:
        result = await asyncio.to_thread(
            generate_diagram, brief, slide_format=slide_format, image_model=image_model,
        )
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception:
        logger.exception("Pipeline failed")
        return JSONResponse({"error": "Pipeline failed. Check server logs."}, status_code=500)

    # Build a relative URL for the generated image
    image_rel = result.image_path.relative_to(settings.output_dir)
    image_url = f"/output/{image_rel}"

    return {
        "image_url": image_url,
        "rounds_taken": result.rounds_taken,
        "approved": result.approved,
        "run_dir": str(result.run_dir),
    }
