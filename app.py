"""SalesBanana Web UI — thin FastAPI wrapper around generate_diagram()."""

import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pathlib import Path

from src.config import IMAGE_MODELS, settings
from src.pipeline import generate_diagram, improve_diagram

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


@app.get("/api/image-models")
async def api_image_models():
    """Return available image generation models for the UI dropdown."""
    return IMAGE_MODELS


@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    brief = body.get("brief", "").strip()
    image_model = body.get("image_model")

    if not brief:
        return JSONResponse({"error": "Brief is required."}, status_code=400)

    if image_model and image_model not in IMAGE_MODELS:
        return JSONResponse({"error": f"Unknown image model: {image_model}"}, status_code=400)

    try:
        result = await asyncio.to_thread(
            generate_diagram, brief, image_model=image_model,
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


@app.post("/api/improve")
async def api_improve(request: Request):
    body = await request.json()
    run_dir_str = body.get("run_dir", "").strip()
    instruction = body.get("instruction", "").strip()
    image_model = body.get("image_model")
    branch_from_round = body.get("branch_from_round")

    if not run_dir_str:
        return JSONResponse({"error": "run_dir is required."}, status_code=400)
    if not instruction:
        return JSONResponse({"error": "Improvement instruction is required."}, status_code=400)
    if image_model and image_model not in IMAGE_MODELS:
        return JSONResponse({"error": f"Unknown image model: {image_model}"}, status_code=400)
    if branch_from_round is not None:
        if not isinstance(branch_from_round, int) or isinstance(branch_from_round, bool) or branch_from_round < 0:
            return JSONResponse({"error": "branch_from_round must be a non-negative integer."}, status_code=400)

    run_dir = Path(run_dir_str).resolve()
    try:
        run_dir.relative_to(settings.output_dir.resolve())
    except ValueError:
        return JSONResponse({"error": "Invalid run directory."}, status_code=400)

    try:
        result = await asyncio.to_thread(
            improve_diagram, run_dir, instruction, image_model=image_model, branch_from_round=branch_from_round,
        )
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception:
        logger.exception("Improvement failed")
        return JSONResponse({"error": "Improvement failed. Check server logs."}, status_code=500)

    image_rel = result.image_path.relative_to(settings.output_dir)
    image_url = f"/output/{image_rel}"

    return {
        "image_url": image_url,
        "round_number": result.round_number,
        "summary": result.summary,
        "approved": result.approved,
        "history": [
            {
                "round_number": r.round_number,
                "summary": r.summary,
                "image_filename": r.image_filename,
                "approved": r.approved,
            }
            for r in result.history
        ],
    }
