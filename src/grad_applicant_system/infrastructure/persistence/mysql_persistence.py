from __future__ import annotations

import os
from typing import Any, Dict, Optional

import mysql.connector
from dotenv import load_dotenv


def _load_env() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(project_root, ".env"))


def _require_env(*keys: str) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")


def _db_connect():
    _load_env()
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


def _next_id(cur, table: str, id_col: str) -> int:
    cur.execute(f"SELECT MAX({id_col}) AS m FROM {table}")
    row = cur.fetchone()
    if not row:
        return 1
    m = row.get("m") if isinstance(row, dict) else row[0]
    return (m or 0) + 1


def _get_or_create_by_name(cur, table: str, id_col: str, name_col: str, name: Optional[str]) -> Optional[int]:
    if not name:
        return None
    # try to find existing
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {name_col} = %s", (name,))
    row = cur.fetchone()
    if row:
        return row.get(id_col) if isinstance(row, dict) else row[0]

    new_id = _next_id(cur, table, id_col)
    cur.execute(
        f"INSERT INTO {table} ({id_col}, {name_col}) VALUES (%s, %s)",
        (new_id, name),
    )
    return new_id


def save_parsed_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Save parsed applicant/program/advisor/application data into the DB.

    The function is tolerant of missing fields. It attempts to reuse existing
    Program/Advisor rows by name, and creates new Applicant and Application
    rows when enough data is present.
    Returns a dict with created/used IDs.
    """
    conn = _db_connect()
    try:
        cur = conn.cursor(dictionary=True)

        result: Dict[str, Optional[int]] = {
            "program_id": None,
            "advisor_id": None,
            "user_id": None,
            "application_id": None,
        }

        # Program
        program_name = data.get("program_major") or data.get("program")
        program_id = _get_or_create_by_name(cur, "Program", "ProgramID", "ProgramMajor", program_name)
        result["program_id"] = program_id

        # Advisor
        advisor_name = data.get("advisor_name")
        advisor_id = _get_or_create_by_name(cur, "Advisor", "AdvisorID", "AdvisorName", advisor_name)
        result["advisor_id"] = advisor_id

        # Applicant
        applicant_name = data.get("applicant_name") or data.get("full_name") or data.get("name")
        if applicant_name:
            # attempt to find by exact name
            cur.execute("SELECT UserID FROM Applicant WHERE ApplicantName = %s", (applicant_name,))
            row = cur.fetchone()
            if row:
                user_id = row.get("UserID") if isinstance(row, dict) else row[0]
            else:
                user_id = _next_id(cur, "Applicant", "UserID")
                cur.execute(
                    "INSERT INTO Applicant (UserID, ApplicantName, UndergraduateGPA, DegreeEarned) VALUES (%s, %s, %s, %s)",
                    (
                        user_id,
                        applicant_name,
                        data.get("undergraduate_gpa"),
                        data.get("degree_earned"),
                    ),
                )
            result["user_id"] = user_id

        # Application
        # create application row if we have at least a user_id and a term
        term = data.get("term_applying_for")
        if result["user_id"] and term:
            application_id = _next_id(cur, "Application", "ApplicationID")
            cur.execute(
                "INSERT INTO Application (ApplicationID, TermApplyingFor, AdmissionDecision, UserID, ProgramID, AdvisorID) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    application_id,
                    term,
                    data.get("admission_decision"),
                    result["user_id"],
                    result["program_id"],
                    result["advisor_id"],
                ),
            )
            result["application_id"] = application_id

        conn.commit()
        return {k: v for k, v in result.items()}

    finally:
        try:
            conn.close()
        except Exception:
            pass
