from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from grad_applicant_system.infrastructure.parsing import (
    PDFDocumentParser,
    SimpleExtractionProcessor,
)


mcp = FastMCP("Capstone Sandbox", stateless_http=True, json_response=True)

parser = PDFDocumentParser()
extractor = SimpleExtractionProcessor()

def _load_env() -> None:
    """Allow running this file directly (outside run.py) while still using .env."""
    project_root = Path(__file__).resolve().parents[1]  # .../capstone_sandbox
    load_dotenv(project_root / ".env")


def _require_env(*keys: str) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")


def _db_connect():
    _require_env("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connection_timeout=5,
    )


def _jsonify(value: Any) -> Any:
    """Convert MySQL-ish types into JSON-safe types."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _jsonify_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _jsonify(v) for k, v in row.items()}


@mcp.tool()
def list_applicants(limit: int = 25) -> dict[str, Any]:
    """
    Return up to N applicants from the MySQL table.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, full_name, email, program, gpa, status, keywords_text, created_at
            FROM applicants
            ORDER BY id
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return {"count": len(rows), "rows": [_jsonify_row(r) for r in rows]}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@mcp.tool()
def get_applicant_by_email(email: str) -> dict[str, Any]:
    """
    Lookup a single applicant by email.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, full_name, email, program, gpa, status, keywords_text, created_at
            FROM applicants
            WHERE email = %s
            """,
            (email,),
        )
        row = cur.fetchone()
        return {"found": bool(row), "row": _jsonify_row(row) if row else None}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@mcp.tool()
def ingest_pdf(file_path: str) -> dict:
    """
    Ingest a PDF, extract structured applicant data
    """

    try:
        text = parser.extract_text(file_path)
        data = extractor.extract(text)

        return {
            "status": "success",
            "file": file_path,
            "data": data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def serve() -> None:
    """
    Run the MCP server over Streamable HTTP.
    Default URL: http://localhost:8000/mcp
    """
    _load_env()

    # Optional: make host/port configurable
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.settings.host = host
    mcp.settings.port = port

    print(f"MCP server listening at http://{host}:{port}/mcp")

    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("\nMCP server stopped.")


if __name__ == "__main__":
    serve()