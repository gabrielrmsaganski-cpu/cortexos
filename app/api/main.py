from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.time_utils import iso_now
from app.demo.seed import seed_demo_dataset
from app.memory.service import get_memory_service
from app.models.schemas import (
    AnswerRequest,
    HealthResponse,
    MemoryInput,
    SearchRequest,
)
from app.product.service import ProductService
from app.tools.crawl4ai_tool import Crawl4AITool
from app.tools.docling_tool import DoclingTool
from app.tools.playwright_tool import PlaywrightTool

configure_logging()
settings = get_settings()
app = FastAPI(title="CortexOS", version="0.1.0")
service = get_memory_service()
product = ProductService()
docling = DoclingTool()
crawler = Crawl4AITool()
playwright = PlaywrightTool()
ui_dist = Path("/home/saganski/workspace/experiments/cortexos/ui/dist")
if (ui_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=ui_dist / "assets"), name="ui-assets")


class WebIngestRequest(BaseModel):
    url: HttpUrl
    wing: str | None = None
    room: str | None = None


class SiteIngestRequest(WebIngestRequest):
    max_pages: int = 3


class EvalRunRequest(BaseModel):
    mode: str = "balanced"


@app.get("/healthz", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    status = service.health()
    overall = "ok" if status["db"] == "ok" and status["qdrant"] == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        api="ok",
        db=status["db"],
        qdrant=status["qdrant"],
        ollama=status["ollama"],
        time=iso_now(),
    )


@app.post("/api/v1/memories")
def add_memory(input_data: MemoryInput):
    return service.add_memory(input_data)


@app.get("/api/v1/memories")
def list_memories(
    search_text: str | None = None,
    wing: str | None = None,
    room: str | None = None,
    memory_type: str | None = None,
    status: str | None = None,
    min_importance: float | None = None,
    max_importance: float | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    conflict_only: bool = False,
    superseded_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return service.list_memories(
        search_text=search_text,
        wing=wing,
        room=room,
        memory_type=memory_type,
        status=status,
        min_importance=min_importance,
        max_importance=max_importance,
        created_from=created_from,
        created_to=created_to,
        conflict_only=conflict_only,
        superseded_only=superseded_only,
        limit=limit,
        offset=offset,
    )


@app.post("/api/v1/memories/preview")
def preview_memory(input_data: MemoryInput):
    return service.preview_memory(input_data)


@app.get("/api/v1/memories/{memory_id}")
def get_memory_detail(memory_id: str):
    detail = service.get_memory_detail(memory_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return detail


@app.get("/api/v1/memories/{memory_id}/compare/{other_id}")
def compare_memories(memory_id: str, other_id: str):
    detail = service.compare_memories(memory_id, other_id)
    if not detail:
        raise HTTPException(status_code=404, detail="One or both memories not found.")
    return detail


@app.post("/api/v1/memories/{memory_id}/archive")
def archive_memory(memory_id: str):
    memory = service.archive_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"memory": memory.model_dump(), "action": "archived"}


@app.post("/api/v1/memories/{memory_id}/reindex")
def reindex_memory(memory_id: str):
    result = service.reindex_memory(memory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return result


@app.post("/api/v1/search")
def search_memory(request: SearchRequest):
    return service.search(request)


@app.post("/api/v1/answer")
def answer_with_memory(request: AnswerRequest):
    return service.answer(request)


@app.post("/api/v1/query-studio")
def query_studio(request: AnswerRequest):
    return service.query_studio(request)


@app.post("/api/v1/ingest/document")
async def ingest_document(
    wing: str = Form(default=settings.default_wing),
    room: str = Form(default=settings.default_room),
    path: str | None = Form(default=None),
    file: Annotated[UploadFile | None, File()] = None,
):
    if path:
        parsed = docling.parse(path)
        return service.add_memory(
            MemoryInput(
                text=parsed["text"],
                wing=wing,
                room=room,
                source="document",
                source_uri=path,
                metadata={"parser": "docling", "available": parsed.get("available", False)},
            )
        )

    if not file:
        return {"error": "Provide either `path` or `file`."}

    suffix = Path(file.filename or "upload.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(await file.read())
        temp_path = handle.name
    parsed = docling.parse(temp_path)
    return service.add_memory(
        MemoryInput(
            text=parsed["text"],
            wing=wing,
            room=room,
            source="document",
            source_uri=file.filename,
            metadata={"parser": "docling", "available": parsed.get("available", False)},
        )
    )


@app.post("/api/v1/ingest/document/preview")
async def preview_document(
    wing: str = Form(default=settings.default_wing),
    room: str = Form(default=settings.default_room),
    path: str | None = Form(default=None),
    file: Annotated[UploadFile | None, File()] = None,
):
    if path:
        parsed = docling.parse(path)
        return {
            "source": path,
            "parser": "docling",
            "available": parsed.get("available", False),
            "preview": service.preview_memory(
                MemoryInput(text=parsed["text"], wing=wing, room=room, source="document-preview")
            ),
        }
    if not file:
        return {"error": "Provide either `path` or `file`."}
    suffix = Path(file.filename or "upload.txt").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(await file.read())
        temp_path = handle.name
    parsed = docling.parse(temp_path)
    return {
        "source": file.filename,
        "parser": "docling",
        "available": parsed.get("available", False),
        "preview": service.preview_memory(
            MemoryInput(text=parsed["text"], wing=wing, room=room, source="document-preview")
        ),
    }


@app.post("/api/v1/ingest/webpage")
async def ingest_webpage(request: WebIngestRequest):
    crawled = await crawler.fetch_page(str(request.url))
    text = crawled.get("markdown") or ""
    if not text:
        rendered = await playwright.render(str(request.url))
        text = rendered.get("text") or ""
    return service.add_memory(
        MemoryInput(
            text=text,
            wing=request.wing or settings.default_wing,
            room=request.room or settings.default_room,
            source="web",
            source_uri=str(request.url),
            metadata={
                "crawl4ai_available": crawled.get("available", False),
                "playwright_available": text != "",
            },
        )
    )


@app.post("/api/v1/ingest/webpage/preview")
async def preview_webpage(request: WebIngestRequest):
    crawled = await crawler.fetch_page(str(request.url))
    text = crawled.get("markdown") or ""
    if not text:
        rendered = await playwright.render(str(request.url))
        text = rendered.get("text") or ""
    return {
        "source": str(request.url),
        "preview_text": text[:5000],
        "preview": service.preview_memory(
            MemoryInput(
                text=text,
                wing=request.wing or settings.default_wing,
                room=request.room or settings.default_room,
                source="web-preview",
            )
        ),
    }


@app.post("/api/v1/ingest/site")
async def ingest_site(request: SiteIngestRequest):
    pages = await crawler.crawl_site(str(request.url), request.max_pages)
    results = []
    for page in pages:
        results.append(
            service.add_memory(
                MemoryInput(
                    text=page.get("markdown", ""),
                    wing=request.wing or settings.default_wing,
                    room=request.room or settings.default_room,
                    source="crawl",
                    source_uri=page.get("url"),
                    metadata={"crawl4ai_available": page.get("available", False)},
                )
            )
        )
    return {"count": len(results), "items": results}


@app.post("/api/v1/ingest/site/preview")
async def preview_site(request: SiteIngestRequest):
    pages = await crawler.crawl_site(str(request.url), request.max_pages)
    previews = []
    for page in pages:
        text = page.get("markdown", "")
        previews.append(
            {
                "url": page.get("url"),
                "available": page.get("available", False),
                "preview_text": text[:2000],
                "classification": service.preview_memory(
                    MemoryInput(
                        text=text,
                        wing=request.wing or settings.default_wing,
                        room=request.room or settings.default_room,
                        source="crawl-preview",
                    )
                ),
            }
        )
    return {"count": len(previews), "items": previews}


@app.get("/api/v1/wings")
def list_wings():
    return {"wings": service.list_wings()}


@app.get("/api/v1/rooms")
def list_rooms(wing: str | None = None):
    return {"rooms": service.list_rooms(wing)}


@app.get("/api/v1/conflicts")
def get_conflicts():
    return {"conflicts": service.get_conflicts()}


@app.get("/api/v1/superseded")
def get_superseded():
    return {"superseded": service.get_superseded()}


@app.post("/api/v1/explain")
def explain_retrieval(request: SearchRequest):
    request.explain = True
    return service.search(request)


@app.get("/api/v1/dashboard")
def dashboard():
    return product.dashboard()


@app.get("/api/v1/timeline")
def timeline(
    wing: str | None = None,
    room: str | None = None,
    memory_type: str | None = None,
    status: str | None = None,
    limit: int = Query(default=250, ge=1, le=1000),
):
    return service.timeline(
        wing=wing,
        room=room,
        memory_type=memory_type,
        status=status,
        limit=limit,
    )


@app.get("/api/v1/operations/status")
def operations_status():
    return product.operations_status()


@app.post("/api/v1/operations/smoke")
def run_smoke():
    return product.run_smoke_test()


@app.get("/api/v1/settings")
def settings_summary():
    return product.settings_summary()


@app.get("/api/v1/evals")
def list_evals():
    return {"items": product.list_eval_runs()}


@app.post("/api/v1/evals/run")
def run_eval(request: EvalRunRequest):
    return product.run_eval(request.mode)


@app.get("/api/v1/evals/{run_id}")
def get_eval(run_id: str):
    item = product.get_eval_run(run_id)
    if not item:
        raise HTTPException(status_code=404, detail="Eval run not found.")
    return item


@app.post("/api/v1/demo/seed")
def seed_demo():
    return seed_demo_dataset()


def run() -> None:
    uvicorn.run("app.api.main:app", host=settings.host, port=settings.port, reload=False)


@app.get("/")
def serve_root():
    if ui_dist.exists():
        return FileResponse(ui_dist / "index.html")
    raise HTTPException(status_code=404, detail="UI build not found.")


@app.get("/{path:path}")
def serve_spa(path: str):
    if path.startswith("api/") or path == "healthz":
        raise HTTPException(status_code=404, detail="Not found.")
    candidate = ui_dist / path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    if ui_dist.exists():
        return FileResponse(ui_dist / "index.html")
    raise HTTPException(status_code=404, detail="UI build not found.")
