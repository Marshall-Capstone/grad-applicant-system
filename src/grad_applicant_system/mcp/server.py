from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


#######################################################################
# Ensure environment is configured
#######################################################################

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

#######################################################################
# MCP Server
#######################################################################   

mcp = FastMCP("Capstone Sandbox", stateless_http=True, json_response=True)

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


def _jsonify(value: Any) -> Any:
    """Convert MySQL-ish types into JSON-safe types."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _jsonify_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: _jsonify(v) for k, v in row.items()}


#######################################################################
# Tools
#######################################################################


@mcp.tool()
def list_applicants(limit: int = 25) -> dict[str, Any]:
    """
    Return up to N applicants from the MySQL schema.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                a.UserID AS user_id,
                a.ApplicantName AS applicant_name,
                a.UndergraduateGPA AS undergraduate_gpa,
                a.DegreeEarned AS degree_earned,
                p.ProgramMajor AS program_major,
                app.TermApplyingFor AS term_applying_for,
                app.AdmissionDecision AS admission_decision,
                adv.AdvisorName AS advisor_name
            FROM Applicant a
            LEFT JOIN Application app ON a.UserID = app.UserID
            LEFT JOIN Program p ON app.ProgramID = p.ProgramID
            LEFT JOIN Advisor adv ON app.AdvisorID = adv.AdvisorID
            ORDER BY a.UserID
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
def list_all_applicants() -> dict[str, Any]:
    """
    Return all applicants from the MySQL schema with accurate count of actual applicants
    There is a limit to what Claude returns so this provides for the best remedy.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                a.UserID AS user_id,
                a.ApplicantName AS applicant_name,
                a.UndergraduateGPA AS undergraduate_gpa,
                a.DegreeEarned AS degree_earned,
                p.ProgramMajor AS program_major,
                app.TermApplyingFor AS term_applying_for,
                app.AdmissionDecision AS admission_decision,
                adv.AdvisorName AS advisor_name
            FROM Applicant a
            LEFT JOIN Application app ON a.UserID = app.UserID
            LEFT JOIN Program p ON app.ProgramID = p.ProgramID
            LEFT JOIN Advisor adv ON app.AdvisorID = adv.AdvisorID
            ORDER BY a.ApplicantName, a.UserID
            """
        )
        rows = cur.fetchall()
        return {"count": len(rows), "rows": [_jsonify_row(r) for r in rows]}
    finally:
        try:
            conn.close()
        except Exception:
            pass

@mcp.tool()
def get_applicant_by_user_id(user_id: int) -> dict[str, Any]:
    """
    Lookup a single applicant by UserID.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                a.UserID AS user_id,
                a.ApplicantName AS applicant_name,
                a.UndergraduateGPA AS undergraduate_gpa,
                a.DegreeEarned AS degree_earned,
                p.ProgramMajor AS program_major,
                app.TermApplyingFor AS term_applying_for,
                app.AdmissionDecision AS admission_decision,
                adv.AdvisorName AS advisor_name
            FROM Applicant a
            LEFT JOIN Application app ON a.UserID = app.UserID
            LEFT JOIN Program p ON app.ProgramID = p.ProgramID
            LEFT JOIN Advisor adv ON app.AdvisorID = adv.AdvisorID
            WHERE a.UserID = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return {"found": bool(row), "row": _jsonify_row(row) if row else None}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@mcp.tool()
def get_applicant_by_gpa(gpa: Decimal, operator: str) -> dict[str, Any]:
    """
    Lookup all applicants with a specific GPA or range of GPAs.
    Operator will be one of the following: 
        greater than ('gt')
        lesser than ('lt')
        equal to ('eq')
        greater than or equal to ('gte')
        lesser than or equal to ('lte')
    """

    OPERATOR_MAP = {
        "gt": ">",
        "lt": "<",
        "eq": "=",
        "gte": ">=",
        "lte": "<="
    }

    if operator not in OPERATOR_MAP:
        raise ValueError(f"Invalid operator: {operator}")

    sql_op = OPERATOR_MAP[operator]

    conn = _db_connect()

    try:
        cur = conn.cursor(dictionary = True)
        cur.execute(
            f"""
            SELECT
                a.UserID AS user_id,
                a.ApplicantName AS applicant_name,
                a.UndergraduateGPA AS undergraduate_gpa,
                a.DegreeEarned AS degree_earned,
                p.ProgramMajor AS program_major,
                app.TermApplyingFor AS term_applying_for,
                app.AdmissionDecision AS admission_decision,
                adv.AdvisorName AS advisor_name
            FROM Applicant a
            LEFT JOIN Application app ON a.UserID = app.UserID
            LEFT JOIN Program p ON app.ProgramID = p.ProgramID
            LEFT JOIN Advisor adv ON app.AdvisorID = adv.AdvisorID
            WHERE a.UndergraduateGPA {sql_op} %s
            """,
            (gpa,),
        )
        rows = cur.fetchall()
        return {"found": bool(rows), "rows": [_jsonify_row(r) for r in rows]}
    finally:
        try:
            conn.close()
        except Exception:
            pass

@mcp.tool()
def get_applicant_by_field(field: str, value: str) -> dict[str, Any]:
    """
    Queries database with a non-GPA field. If user searches with an id, it must be an exact match. 
    If not, values similar to input are allowed.
    """
    EXACT_FIELDS = {
        "user_id":        "a.UserID",
        "program_id":     "p.ProgramID",
        "advisor_id":     "adv.AdvisorID",
        "application_id": "app.ApplicationID"
    }

    LIKE_FIELDS = {
        "applicant_name":     "a.ApplicantName",
        "degree_earned":      "a.DegreeEarned",
        "program_major":      "p.ProgramMajor",
        "advisor_name":       "adv.AdvisorName",
        "term_applying_for":  "app.TermApplyingFor",
        "admission_decision": "app.AdmissionDecision"
    }

    if field in EXACT_FIELDS:
        sql_field = EXACT_FIELDS[field]
        sql_value = value
        condition = f"{sql_field} = %s"
    elif field in LIKE_FIELDS:
        sql_field = LIKE_FIELDS[field]
        sql_value = f"%{value}%"
        condition = f"{sql_field} LIKE %s"
    else:
        raise ValueError(f"Invalid field: {field}")

    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"""
            SELECT
                a.UserID AS user_id,
                a.ApplicantName AS applicant_name,
                a.UndergraduateGPA AS undergraduate_gpa,
                a.DegreeEarned AS degree_earned,
                p.ProgramMajor AS program_major,
                app.TermApplyingFor AS term_applying_for,
                app.AdmissionDecision AS admission_decision,
                adv.AdvisorName AS advisor_name
            FROM Applicant a
            LEFT JOIN Application app ON a.UserID = app.UserID
            LEFT JOIN Program p ON app.ProgramID = p.ProgramID
            LEFT JOIN Advisor adv ON app.AdvisorID = adv.AdvisorID
            WHERE {condition}
            """,
            (sql_value,),
        )
        rows = cur.fetchall()
        return {"found": bool(rows), "rows": [_jsonify_row(r) for r in rows]}
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    serve()