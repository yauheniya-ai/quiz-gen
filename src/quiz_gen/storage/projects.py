"""Project management — persistent storage for quiz-gen.

Filesystem layout under ``~/.quiz-gen/``:

  registry.db                      – shared project registry
  {project}/documents/             – raw HTML files (one per parsed document)
  {project}/quizzes/               – generated quiz JSON files
  {project}/debug/                 – full agent debug/trace JSON
  {project}/data/project.db        – per-project SQLite (documents + quizzes tables)
"""

from __future__ import annotations

import json as _json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Filesystem layout
# ---------------------------------------------------------------------------

QUIZ_GEN_HOME: Path = Path.home() / ".quiz-gen"
REGISTRY_DB: Path = QUIZ_GEN_HOME / "registry.db"
DEFAULT_PROJECT: str = "default"
PROJECT_SUBDIRS = ("documents", "quizzes", "debug", "data")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _ensure_home() -> None:
    QUIZ_GEN_HOME.mkdir(parents=True, exist_ok=True)


def _registry_conn() -> sqlite3.Connection:
    _ensure_home()
    conn = sqlite3.connect(REGISTRY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_registry() -> None:
    """Create registry table and seed the default project."""
    with _registry_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                name        TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO projects (name, created_at) VALUES (?, ?)",
            (DEFAULT_PROJECT, _now_iso()),
        )
        conn.commit()


def _project_root(name: str) -> Path:
    return QUIZ_GEN_HOME / name


def _ensure_project_dirs(name: str) -> Path:
    root = _project_root(name)
    for sub in PROJECT_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _project_db_path(name: str) -> Path:
    return _project_root(name) / "data" / "project.db"


def _init_project_db(name: str) -> None:
    """Create / migrate tables inside a project's own SQLite database."""
    db = _project_db_path(name)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                type        TEXT NOT NULL,
                url         TEXT,
                created_at  TEXT NOT NULL,
                chunks_json TEXT,
                toc_json    TEXT
            )
            """
        )
        # Migrate: add toc_json column if it was created without it
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN toc_json TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id              TEXT PRIMARY KEY,
                document_id     TEXT,
                section_title   TEXT,
                section_type    TEXT,
                created_at      TEXT NOT NULL,
                config_json     TEXT,
                questions_json  TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
            """
        )
        conn.commit()


def _project_stats(name: str) -> dict:
    root = _project_root(name)
    size_kb, doc_count, quiz_count = 0, 0, 0
    if root.exists():
        try:
            size_kb = sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) // 1024
        except OSError:
            pass
        db = _project_db_path(name)
        if db.exists():
            try:
                with sqlite3.connect(db) as conn:
                    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
                    quiz_count = conn.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
            except sqlite3.DatabaseError:
                pass
    return {"size_kb": size_kb, "documents": doc_count, "quizzes": quiz_count}


# ---------------------------------------------------------------------------
# Public project management
# ---------------------------------------------------------------------------

def list_projects(active_project: Optional[str] = None) -> list[dict]:
    _init_registry()
    with _registry_conn() as conn:
        rows = conn.execute(
            "SELECT name, description, created_at FROM projects ORDER BY name"
        ).fetchall()
    result = []
    for row in rows:
        name = row["name"]
        root = _project_root(name)
        stats = _project_stats(name)
        is_active = (name == active_project) if active_project else (name == DEFAULT_PROJECT)
        result.append({
            "name":        name,
            "path":        str(root),
            "root":        str(QUIZ_GEN_HOME),
            "description": row["description"],
            "size_kb":     stats["size_kb"],
            "documents":   stats["documents"],
            "quizzes":     stats["quizzes"],
            "is_default":  name == DEFAULT_PROJECT,
            "is_active":   is_active,
            "exists":      root.exists(),
            "created_at":  row["created_at"],
        })
    return result


def create_project(name: str, description: str = "") -> dict:
    _init_registry()
    with _registry_conn() as conn:
        if conn.execute("SELECT 1 FROM projects WHERE name = ?", (name,)).fetchone():
            raise ValueError(f"Project '{name}' already exists.")
        conn.execute(
            "INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
            (name, description, _now_iso()),
        )
        conn.commit()
    _ensure_project_dirs(name)
    _init_project_db(name)
    root = _project_root(name)
    return {
        "name":        name,
        "path":        str(root),
        "root":        str(QUIZ_GEN_HOME),
        "description": description,
        "size_kb":     0,
        "documents":   0,
        "quizzes":     0,
        "is_default":  name == DEFAULT_PROJECT,
        "is_active":   True,
        "exists":      True,
        "created_at":  _now_iso(),
    }


def delete_project(name: str, keep_files: bool = False) -> None:
    if name == DEFAULT_PROJECT:
        raise ValueError("The default project cannot be deleted.")
    _init_registry()
    with _registry_conn() as conn:
        conn.execute("DELETE FROM projects WHERE name = ?", (name,))
        conn.commit()
    if not keep_files:
        root = _project_root(name)
        if root.exists():
            shutil.rmtree(root)


def get_project_root(name: str) -> Path:
    """Return the project root path, ensuring all subdirectories exist."""
    _ensure_project_dirs(name)
    _init_project_db(name)
    return _project_root(name)


# ---------------------------------------------------------------------------
# Persistence helpers — called by API endpoints after parse / generate
# ---------------------------------------------------------------------------

def save_document(
    project: str,
    doc_id: str,
    name: str,
    doc_type: str,
    url: Optional[str],
    html_content: Optional[str],
    chunks_json: Optional[str] = None,
    toc_json: Optional[str] = None,
) -> Path:
    """Save a parsed document: HTML file + SQLite row.

    Saves raw HTML to ``documents/<doc_id>.html`` and upserts a row in the
    project's ``documents`` table.  Returns the path to the saved HTML file.
    """
    root = _ensure_project_dirs(project)
    _init_project_db(project)

    docs_dir = root / "documents"
    html_path = docs_dir / f"{doc_id}.html"
    if html_content:
        html_path.write_text(html_content, encoding="utf-8")

    db = _project_db_path(project)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (id, name, type, url, created_at, chunks_json, toc_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, name, doc_type, url, _now_iso(), chunks_json, toc_json),
        )
        conn.commit()

    return html_path if html_content else docs_dir


def save_quiz(
    project: str,
    quiz_id: str,
    document_id: Optional[str],
    section_title: Optional[str],
    section_type: Optional[str],
    config_dict: dict,
    questions: list,
    full_result: dict,
) -> Path:
    """Save a generated quiz: JSON file + SQLite row."""
    root = _ensure_project_dirs(project)
    _init_project_db(project)

    quiz_path = root / "quizzes" / f"{quiz_id}.json"
    quiz_path.write_text(_json.dumps(full_result, ensure_ascii=False, indent=2), encoding="utf-8")

    db = _project_db_path(project)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO quizzes
                (id, document_id, section_title, section_type,
                 created_at, config_json, questions_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_id,
                document_id,
                section_title,
                section_type,
                _now_iso(),
                _json.dumps(config_dict),
                _json.dumps(questions, ensure_ascii=False),
            ),
        )
        conn.commit()

    return quiz_path


def save_debug(project: str, quiz_id: str, debug_data: dict) -> Path:
    """Write full debug/trace JSON to debug/<quiz_id>.json."""
    root = _ensure_project_dirs(project)
    debug_path = root / "debug" / f"{quiz_id}.json"
    debug_path.write_text(_json.dumps(debug_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return debug_path


# ---------------------------------------------------------------------------
# Query helpers — called by API read endpoints
# ---------------------------------------------------------------------------

def list_project_documents(project: str) -> list[dict]:
    """Return lightweight metadata for all documents in a project (no content blobs)."""
    db = _project_db_path(project)
    if not db.exists():
        return []
    _init_project_db(project)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, type, url, created_at FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_project_document(project: str, doc_id: str) -> Optional[dict]:
    """Return full document data including parsed chunks and TOC."""
    db = _project_db_path(project)
    if not db.exists():
        return None
    _init_project_db(project)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name, type, url, created_at, chunks_json, toc_json FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
    if not row:
        return None
    doc = dict(row)
    doc["chunks"] = _json.loads(doc.pop("chunks_json") or "[]")
    doc["toc"]    = _json.loads(doc.pop("toc_json")    or "null")
    return doc


def list_project_quizzes(project: str) -> list[dict]:
    """Return lightweight metadata for all quizzes in a project."""
    db = _project_db_path(project)
    if not db.exists():
        return []
    _init_project_db(project)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, document_id, section_title, section_type, created_at, questions_json
            FROM quizzes
            ORDER BY created_at DESC
            """
        ).fetchall()
    result = []
    for r in rows:
        entry = dict(r)
        questions = _json.loads(entry.pop("questions_json") or "[]")
        entry["question_count"] = len(questions)
        result.append(entry)
    return result


def get_project_quiz(project: str, quiz_id: str) -> Optional[dict]:
    """Return full quiz data (from the JSON file if available, else from DB)."""
    quiz_path = _project_root(project) / "quizzes" / f"{quiz_id}.json"
    if quiz_path.exists():
        return _json.loads(quiz_path.read_text(encoding="utf-8"))

    db = _project_db_path(project)
    if not db.exists():
        return None
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, document_id, section_title, section_type, created_at, questions_json, config_json FROM quizzes WHERE id = ?",
            (quiz_id,),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["questions"] = _json.loads(data.pop("questions_json") or "[]")
    data["config"]    = _json.loads(data.pop("config_json")    or "{}")
    return data


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


# ── Project CRUD ─────────────────────────────────────────────────────────────

@router.get("/projects")
def api_list_projects(active_project: Optional[str] = None):
    return {"projects": list_projects(active_project)}


@router.post("/projects", status_code=201)
def api_create_project(body: CreateProjectRequest):
    try:
        return create_project(body.name, body.description)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/projects/{name}")
def api_delete_project(name: str, keep_files: bool = False):
    try:
        delete_project(name, keep_files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted", "name": name}


# ── Documents ────────────────────────────────────────────────────────────────

@router.get("/projects/{project}/documents")
def api_list_documents(project: str):
    """List all documents stored in a project."""
    return {"documents": list_project_documents(project)}


@router.get("/projects/{project}/documents/{doc_id}")
def api_get_document(project: str, doc_id: str):
    """Return chunks and TOC for a stored document."""
    doc = get_project_document(project, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found in project '{project}'.")
    return doc


@router.delete("/projects/{project}/documents/{doc_id}")
def api_delete_document(project: str, doc_id: str):
    """Delete a document (DB row + HTML file) from a project."""
    db = _project_db_path(project)
    if not db.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found.")
    _init_project_db(project)
    with sqlite3.connect(db) as conn:
        deleted = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,)).rowcount
        conn.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    # Remove the HTML file if it exists
    html_path = _project_root(project) / "documents" / f"{doc_id}.html"
    if html_path.exists():
        html_path.unlink()
    return {"status": "deleted", "id": doc_id}


# ── Quizzes ───────────────────────────────────────────────────────────────────

@router.get("/projects/{project}/quizzes")
def api_list_quizzes(project: str):
    """List all quizzes stored in a project."""
    return {"quizzes": list_project_quizzes(project)}


@router.get("/projects/{project}/quizzes/{quiz_id}")
def api_get_quiz(project: str, quiz_id: str):
    """Return full quiz data for a stored quiz."""
    quiz = get_project_quiz(project, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found in project '{project}'.")
    return quiz
