#!/usr/bin/env python3
"""explore_db.py – Print everything stored in ~/.quiz-gen/

Usage:
    python examples/explore_db.py            # all projects
    python examples/explore_db.py ai-act     # one project only
    python examples/explore_db.py --json     # output as JSON
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

QUIZ_GEN_HOME = Path.home() / ".quiz-gen"
REGISTRY_DB   = QUIZ_GEN_HOME / "registry.db"

# ── ANSI colours (degrade gracefully if not a tty) ──────────────────────────
import sys
_no_color = not sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if _no_color:
        return text
    return f"\033[{code}m{text}\033[0m"

BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)
CYAN   = lambda t: _c("96",   t)
GREEN  = lambda t: _c("92",   t)
YELLOW = lambda t: _c("93",   t)
RED    = lambda t: _c("91",   t)
BLUE   = lambda t: _c("94",   t)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _hr(char: str = "─", width: int = 72) -> str:
    return char * width


def _truncate(text: str, max_len: int = 120) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _fmt_size(kb: int) -> str:
    if kb < 1024:
        return f"{kb} KB"
    return f"{kb / 1024:.1f} MB"


# ── Registry ─────────────────────────────────────────────────────────────────

def load_registry() -> list[dict]:
    if not REGISTRY_DB.exists():
        return []
    with _conn(REGISTRY_DB) as conn:
        try:
            rows = conn.execute(
                "SELECT name, description, created_at FROM projects ORDER BY name"
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.DatabaseError:
            return []


# ── Per-project data ──────────────────────────────────────────────────────────

def load_project(name: str) -> dict:
    root = QUIZ_GEN_HOME / name
    db   = root / "data" / "project.db"

    result: dict = {
        "name":      name,
        "root":      str(root),
        "exists":    root.exists(),
        "documents": [],
        "quizzes":   [],
        "files":     {},
    }

    # File counts
    for sub in ("documents", "quizzes", "debug"):
        d = root / sub
        result["files"][sub] = sorted(str(p) for p in d.glob("*") if p.is_file()) if d.exists() else []

    if not db.exists():
        return result

    with _conn(db) as conn:
        # Documents
        try:
            docs = conn.execute(
                "SELECT id, name, type, url, created_at FROM documents ORDER BY created_at"
            ).fetchall()
            result["documents"] = [dict(r) for r in docs]
        except sqlite3.DatabaseError:
            pass

        # Quizzes
        try:
            quizzes = conn.execute(
                """SELECT id, document_id, section_title, section_type,
                          created_at, questions_json
                   FROM quizzes ORDER BY created_at"""
            ).fetchall()
            quiz_rows = []
            for r in quizzes:
                row = dict(r)
                try:
                    qs = json.loads(row.get("questions_json") or "[]")
                    row["question_count"] = len(qs)
                    row["questions_preview"] = [
                        q.get("question") or q.get("text", "?")
                        for q in qs[:3]
                    ]
                except (json.JSONDecodeError, TypeError):
                    row["question_count"] = 0
                    row["questions_preview"] = []
                quiz_rows.append(row)
            result["quizzes"] = quiz_rows
        except sqlite3.DatabaseError:
            pass

    return result


# ── Pretty-print ──────────────────────────────────────────────────────────────

def print_project(proj: dict) -> None:
    name = proj["name"]
    print()
    print(_hr("═"))
    print(BOLD(CYAN(f"  PROJECT: {name}")), DIM(f"  ({proj['root']})"))
    print(_hr("═"))

    if not proj["exists"]:
        print(RED("  ✗ directory does not exist on disk"))
        return

    # ── Documents ───────────────────────────────────────────────────────────
    docs = proj["documents"]
    doc_files = proj["files"].get("documents", [])
    print()
    print(BOLD(GREEN(f"  📄 Documents  (db rows: {len(docs)}, files: {len(doc_files)})")))
    if docs:
        for d in docs:
            print(f"    {YELLOW(d['id'])}")
            print(f"      name : {d['name']}")
            print(f"      type : {d['type']}")
            if d.get('url'):
                print(f"      url  : {_truncate(d['url'], 80)}")
            print(f"      saved: {d['created_at']}")
    else:
        print(DIM("    (none)"))

    if doc_files:
        print(DIM("  Files on disk:"))
        for f in doc_files:
            size = Path(f).stat().st_size
            print(DIM(f"    {_fmt_size(size // 1024 or 1):>8}  {f}"))

    # ── Quizzes ──────────────────────────────────────────────────────────────
    quizzes = proj["quizzes"]
    qz_files = proj["files"].get("quizzes", [])
    print()
    print(BOLD(BLUE(f"  🧠 Quizzes    (db rows: {len(quizzes)}, files: {len(qz_files)})")))
    if quizzes:
        for q in quizzes:
            print(f"    {YELLOW(q['id'])}")
            print(f"      section : {q.get('section_title', '?')}  [{q.get('section_type', '?')}]")
            print(f"      doc_id  : {q.get('document_id', '—')}")
            print(f"      saved   : {q['created_at']}")
            print(f"      questions ({q['question_count']}):")
            for i, text in enumerate(q["questions_preview"], 1):
                print(f"        {i}. {_truncate(str(text), 100)}")
            if q["question_count"] > 3:
                print(DIM(f"        … and {q['question_count'] - 3} more"))
    else:
        print(DIM("    (none)"))

    # ── Debug files ──────────────────────────────────────────────────────────
    dbg_files = proj["files"].get("debug", [])
    if dbg_files:
        print()
        print(BOLD(f"  🔍 Debug files ({len(dbg_files)})"))
        for f in dbg_files:
            size = Path(f).stat().st_size
            print(DIM(f"    {_fmt_size(size // 1024 or 1):>8}  {f}"))


# ── JSON output ───────────────────────────────────────────────────────────────

def dump_json(projects: list[dict]) -> None:
    # Strip binary / huge fields that don't JSON-serialise well
    out = []
    for p in projects:
        clean = {k: v for k, v in p.items() if k != "html_content"}
        out.append(clean)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explore ~/.quiz-gen project databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Project name to inspect (default: all projects)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of pretty-print",
    )
    args = parser.parse_args()

    if not QUIZ_GEN_HOME.exists():
        print(RED(f"✗ ~/.quiz-gen does not exist yet."))
        print("  Run `quiz-gen --ui` and create a project first.")
        return

    registry = load_registry()

    if not registry:
        print(YELLOW("No projects registered in ~/.quiz-gen/registry.db"))
        # Still scan directories
        found = [d.name for d in sorted(QUIZ_GEN_HOME.iterdir()) if d.is_dir()]
        if found:
            print(f"  Found directories: {', '.join(found)}")
            registry = [{"name": n, "description": "", "created_at": "?"} for n in found]
        else:
            return

    if args.project:
        names = [args.project]
    else:
        names = [r["name"] for r in registry]

    projects = [load_project(n) for n in names]

    if args.json:
        dump_json(projects)
        return

    # Header
    print()
    print(BOLD(f"  quiz-gen database explorer"))
    print(DIM(f"  Location: {QUIZ_GEN_HOME}"))
    print(DIM(f"  Registry: {REGISTRY_DB}"))
    print(DIM(f"  Projects: {', '.join(names)}"))

    for proj in projects:
        print_project(proj)

    print()
    print(_hr())
    total_docs   = sum(len(p["documents"]) for p in projects)
    total_quizzes = sum(len(p["quizzes"]) for p in projects)
    print(BOLD(f"  Total  {total_docs} document(s), {total_quizzes} quiz run(s) across {len(projects)} project(s)"))
    print()


if __name__ == "__main__":
    main()
