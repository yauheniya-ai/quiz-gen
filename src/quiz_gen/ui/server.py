from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from quiz_gen import EURLexParser
from .api import router as quiz_router
from ..storage import router as projects_router, save_document
from typing import Dict, Any
import httpx
import json as _json

BASE_DIR = Path(__file__).parent.parent.parent.parent  # quiz-gen/
STATIC_DIR = BASE_DIR / "src" / "quiz_gen" / "ui" / "static"

app = FastAPI(title="Quiz Gen – API", description="", version="0.1.0")

# Cache for HTML documents and their metadata
html_cache: Dict[str, str] = {}
html_metadata: Dict[str, dict] = {}  # Store metadata like source type

# Mount quiz API
app.include_router(quiz_router)
# Mount project management API
app.include_router(projects_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    return FileResponse(favicon_path)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.178.37:5173",
        "https://yauheniya-ai.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {"status": "healthy", "api": "ready"}


# Request/Response Models
class ParseDocumentRequest(BaseModel):
    url: str
    doc_id: str
    project: str = "default"
    doc_name: str | None = None


class TOCItem(BaseModel):
    title: str
    level: int
    section_id: str


class Chunk(BaseModel):
    content: str
    section_type: str
    citation: str
    metadata: Dict[str, Any]


# API Endpoints
@app.post("/api/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse EU-Lex document and return TOC and chunks"""
    try:
        parser = EURLexParser(url=request.url)
        chunks, toc = parser.parse()
        # Fetch and cache the HTML document for preview (with timeout)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(request.url)
                if response.status_code == 200:
                    html_cache[request.doc_id] = response.text
                    html_metadata[request.doc_id] = {
                        "source": "url",
                        "url": request.url,
                    }
                else:
                    pass
        except Exception:
            pass
        chunks_data = [
            {
                "content": chunk.content,
                "section_type": (
                    chunk.section_type.value
                    if hasattr(chunk.section_type, "value")
                    else str(chunk.section_type)
                ),
                "number": getattr(chunk, "number", None),
                "title": chunk.title,
                "hierarchy_path": chunk.hierarchy_path,
                "metadata": chunk.metadata if hasattr(chunk, "metadata") else {},
            }
            for chunk in chunks
        ]
        chunk_id_map = {}
        for chunk in chunks:
            metadata = chunk.metadata if hasattr(chunk, "metadata") else {}
            if metadata and "id" in metadata:
                section_type_str = (
                    chunk.section_type.value
                    if hasattr(chunk.section_type, "value")
                    else str(chunk.section_type)
                )
                if hasattr(chunk, "number") and chunk.number:
                    key = (section_type_str, chunk.number)
                else:
                    key = (section_type_str, None)
                chunk_id_map[key] = metadata["id"]

        def serialize_toc(toc_item):
            if isinstance(toc_item, dict):
                result = {
                    "type": toc_item.get("type", "unknown"),
                    "title": toc_item.get("title", ""),
                }
                if "number" in toc_item and toc_item["number"]:
                    result["number"] = toc_item["number"]
                if "metadata_id" in toc_item and toc_item["metadata_id"]:
                    result["metadata_id"] = toc_item["metadata_id"]
                else:
                    toc_type = toc_item.get("type")
                    toc_number = toc_item.get("number")
                    key = (toc_type, toc_number) if toc_number else (toc_type, None)
                    if key in chunk_id_map:
                        result["metadata_id"] = chunk_id_map[key]
                if "children" in toc_item and toc_item["children"]:
                    result["children"] = [
                        serialize_toc(child) for child in toc_item["children"]
                    ]
                return result
            result = {
                "type": getattr(toc_item, "type", "unknown"),
                "title": getattr(toc_item, "title", ""),
            }
            if hasattr(toc_item, "number") and toc_item.number:
                result["number"] = toc_item.number
            if hasattr(toc_item, "metadata_id") and toc_item.metadata_id:
                result["metadata_id"] = toc_item.metadata_id
            else:
                toc_type = getattr(toc_item, "type", None)
                toc_number = getattr(toc_item, "number", None)
                key = (toc_type, toc_number) if toc_number else (toc_type, None)
                if key in chunk_id_map:
                    result["metadata_id"] = chunk_id_map[key]
            if hasattr(toc_item, "children") and toc_item.children:
                result["children"] = [
                    serialize_toc(child) for child in toc_item.children
                ]
            return result

        if isinstance(toc, dict):
            toc_data = {
                "title": toc.get("title", "Regulation"),
                "sections": [
                    serialize_toc(section) for section in toc.get("sections", [])
                ],
            }
        else:
            toc_data = {
                "title": getattr(toc, "title", "Regulation"),
                "sections": [
                    serialize_toc(section) for section in getattr(toc, "sections", [])
                ],
            }
        title_chunk = next(
            (
                c
                for c in chunks
                if (
                    c.section_type == "title"
                    or (
                        hasattr(c.section_type, "value")
                        and c.section_type.value == "title"
                    )
                    or str(c.section_type) == "title"
                    or str(c.section_type) == "SectionType.TITLE"
                )
            ),
            None,
        )
        if title_chunk:
            has_title = any(
                (
                    s.get("type") == "title"
                    if isinstance(s, dict)
                    else getattr(s, "type", None) == "title"
                )
                for s in (toc_data["sections"] if isinstance(toc_data, dict) else [])
            )
            if not has_title:
                title_metadata = (
                    title_chunk.metadata if hasattr(title_chunk, "metadata") else {}
                )
                title_section = {
                    "type": "title",
                    "title": title_chunk.title,
                    "metadata_id": title_metadata.get("id") if title_metadata else None,
                }
                toc_data["sections"] = [title_section] + toc_data["sections"]
        # ── Persist document to project ─────────────────────────────
        try:
            cached_html = html_cache.get(request.doc_id)
            save_document(
                project=request.project,
                doc_id=request.doc_id,
                name=request.doc_name or request.url,
                doc_type="url",
                url=request.url,
                html_content=cached_html,
                chunks_json=_json.dumps(chunks_data),                toc_json=_json.dumps(toc_data),            )
        except Exception as save_err:
            print(f"[projects] Failed to save document {request.doc_id}: {save_err}")

        return {
            "success": True,
            "doc_id": request.doc_id,
            "chunks": chunks_data,
            "toc": toc_data,
            "total_chunks": len(chunks_data),
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...), doc_id: str = Form(...), project: str = Form("default")):
    """Parse uploaded HTML file and return TOC and chunks"""
    try:
        html_content = await file.read()
        html_text = html_content.decode("utf-8")
        parser = EURLexParser(html_content=html_text)
        chunks, toc = parser.parse()
        html_cache[doc_id] = html_text
        html_metadata[doc_id] = {"source": "upload", "filename": file.filename}
        chunks_data = [
            {
                "content": chunk.content,
                "section_type": (
                    chunk.section_type.value
                    if hasattr(chunk.section_type, "value")
                    else str(chunk.section_type)
                ),
                "number": getattr(chunk, "number", None),
                "title": chunk.title,
                "hierarchy_path": chunk.hierarchy_path,
                "metadata": chunk.metadata if hasattr(chunk, "metadata") else {},
            }
            for chunk in chunks
        ]
        chunk_id_map = {}
        for chunk in chunks:
            metadata = chunk.metadata if hasattr(chunk, "metadata") else {}
            if metadata and "id" in metadata:
                section_type_str = (
                    chunk.section_type.value
                    if hasattr(chunk.section_type, "value")
                    else str(chunk.section_type)
                )
                if hasattr(chunk, "number") and chunk.number:
                    key = (section_type_str, chunk.number)
                else:
                    key = (section_type_str, None)
                chunk_id_map[key] = metadata["id"]

        def serialize_toc(toc_item):
            if isinstance(toc_item, dict):
                result = {
                    "type": toc_item.get("type", "unknown"),
                    "title": toc_item.get("title", ""),
                }
                if "number" in toc_item and toc_item["number"]:
                    result["number"] = toc_item["number"]
                if "metadata_id" in toc_item:
                    result["metadata_id"] = toc_item["metadata_id"]
                if "children" in toc_item:
                    result["children"] = [
                        serialize_toc(child) for child in toc_item["children"]
                    ]
                return result
            result = {
                "type": getattr(toc_item, "type", "unknown"),
                "title": getattr(toc_item, "title", ""),
            }
            if hasattr(toc_item, "number") and toc_item.number:
                result["number"] = toc_item.number
            if hasattr(toc_item, "metadata_id") and toc_item.metadata_id:
                result["metadata_id"] = toc_item.metadata_id
            else:
                toc_type = getattr(toc_item, "type", None)
                toc_number = getattr(toc_item, "number", None)
                key = (toc_type, toc_number) if toc_number else (toc_type, None)
                if key in chunk_id_map:
                    result["metadata_id"] = chunk_id_map[key]
            if hasattr(toc_item, "children") and toc_item.children:
                result["children"] = [
                    serialize_toc(child) for child in toc_item.children
                ]
            return result

        if isinstance(toc, dict):
            toc_data = {
                "title": toc.get("title", "Document"),
                "sections": [
                    serialize_toc(section) for section in toc.get("sections", [])
                ],
            }
        else:
            toc_data = {
                "title": getattr(toc, "title", "Document"),
                "sections": [
                    serialize_toc(section) for section in getattr(toc, "sections", [])
                ],
            }
        title_chunk = next(
            (
                c
                for c in chunks
                if (
                    c.section_type == "title"
                    or (
                        hasattr(c.section_type, "value")
                        and c.section_type.value == "title"
                    )
                    or str(c.section_type) == "title"
                    or str(c.section_type) == "SectionType.TITLE"
                )
            ),
            None,
        )
        if title_chunk:
            has_title = any(
                (
                    s.get("type") == "title"
                    if isinstance(s, dict)
                    else getattr(s, "type", None) == "title"
                )
                for s in (toc_data["sections"] if isinstance(toc_data, dict) else [])
            )
            if not has_title:
                title_metadata = (
                    title_chunk.metadata if hasattr(title_chunk, "metadata") else {}
                )
                title_section = {
                    "type": "title",
                    "title": title_chunk.title,
                    "metadata_id": title_metadata.get("id") if title_metadata else None,
                }
                toc_data["sections"] = [title_section] + toc_data["sections"]
        # ── Persist document to project ──────────────────────────────────────
        try:
            save_document(
                project=project,
                doc_id=doc_id,
                name=file.filename or doc_id,
                doc_type="html",
                url=None,
                html_content=html_text,
                chunks_json=_json.dumps(chunks_data),
                toc_json=_json.dumps(toc_data),
            )
        except Exception as save_err:
            print(f"[projects] Failed to save document {doc_id}: {save_err}")

        return {
            "success": True,
            "doc_id": doc_id,
            "chunks": chunks_data,
            "toc": toc_data,
            "total_chunks": len(chunks_data),
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chunk/{doc_id}/{chunk_index}")
async def get_chunk(doc_id: str, chunk_index: int):
    return {"error": "Not implemented"}


@app.get("/api/document/{doc_id}", response_class=HTMLResponse)
async def get_document_html(doc_id: str):
    if doc_id not in html_cache:
        raise HTTPException(
            status_code=404, detail="Document not found. Please parse it first."
        )
    html_content = html_cache[doc_id]
    metadata = html_metadata.get(doc_id, {})
    if metadata.get("source") == "url" and "<head>" in html_content:
        html_content = html_content.replace(
            "<head>", '<head><base href="https://eur-lex.europa.eu/">', 1
        )
    return HTMLResponse(content=html_content)


# Serve static frontend — must be last so API routes take priority
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
