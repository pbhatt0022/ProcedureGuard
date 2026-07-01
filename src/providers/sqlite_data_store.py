from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteDataStore:
    """SQLite-backed read-only provider seeded from local dummy JSON data."""

    def __init__(self, db_path: str | Path | None = None, data_dir: Path | None = None) -> None:
        default_db_path = Path(__file__).resolve().parent.parent / "local_data" / "procedureguard.db"
        self._db_path = Path(db_path) if db_path is not None else default_db_path
        self._data_dir = data_dir or Path(__file__).resolve().parent.parent / "dummy_data"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def query_verdicts(self, run_id: str, step_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT payload FROM verdicts WHERE run_id = ?"
        params: list[Any] = [self._normalize(run_id)]
        if step_id is not None:
            sql += " AND step_id = ?"
            params.append(self._normalize(step_id))
        return self._fetch_payloads(sql, params)

    def fetch_keyframes(
        self,
        run_id: str,
        step_id: str | None = None,
        timestamp: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._query_evidence("keyframe", run_id, step_id, timestamp)

    def fetch_video_clips(
        self,
        run_id: str,
        step_id: str | None = None,
        timestamp: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._query_evidence("video_clip", run_id, step_id, timestamp)

    def retrieve_ticket_status(self, ticket_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT payload FROM tickets WHERE ticket_id = ?",
            [self._normalize(ticket_id)],
        )

    def query_tickets(self, run_id: str, step_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT payload FROM tickets WHERE run_id = ?"
        params: list[Any] = [self._normalize(run_id)]
        if step_id is not None:
            sql += " AND step_id = ?"
            params.append(self._normalize(step_id))
        return self._fetch_payloads(sql, params)

    def query_incidents(
        self,
        run_id: str,
        step_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT payload FROM incidents WHERE run_id = ?"
        params: list[Any] = [self._normalize(run_id)]
        if step_id is not None:
            sql += " AND step_id = ?"
            params.append(self._normalize(step_id))
        if severity is not None:
            sql += " AND severity = ?"
            params.append(self._normalize(severity))
        if status is not None:
            sql += " AND status = ?"
            params.append(self._normalize(status))
        return self._fetch_payloads(sql, params)

    def retrieve_incident(self, incident_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT payload FROM incidents WHERE incident_id = ?",
            [self._normalize(incident_id)],
        )

    def query_audit_logs(
        self,
        run_id: str,
        step_id: str | None = None,
        ticket_id: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT payload FROM audit_logs WHERE run_id = ?"
        params: list[Any] = [self._normalize(run_id)]
        if step_id is not None:
            sql += " AND step_id = ?"
            params.append(self._normalize(step_id))
        if ticket_id is not None:
            sql += " AND (ticket_id = ? OR incident_id = ?)"
            normalized_ticket_id = self._normalize(ticket_id)
            params.extend([normalized_ticket_id, normalized_ticket_id])
        sql += " ORDER BY timestamp ASC"
        return self._fetch_payloads(sql, params)

    def get_evidence_by_ids(self, evidence_ids: list[str]) -> list[dict[str, Any]]:
        wanted = [self._normalize(evidence_id) for evidence_id in evidence_ids if evidence_id]
        if not wanted:
            return []
        placeholders = ", ".join("?" for _ in wanted)
        return self._fetch_payloads(
            f"SELECT payload FROM evidence WHERE evidence_id IN ({placeholders})",
            wanted,
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT payload FROM runs WHERE run_id = ?",
            [self._normalize(run_id)],
        )

    def retrieve_run_summary(self, run_id: str) -> dict[str, Any] | None:
        return self.get_run(run_id)

    def retrieve_checklist_step(self, run_id: str, step_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT payload FROM checklist_steps WHERE run_id = ? AND step_id = ?",
            [self._normalize(run_id), self._normalize(step_id)],
        )

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS checklist_steps (
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    sequence_number INTEGER,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (run_id, step_id)
                );
                CREATE TABLE IF NOT EXISTS verdicts (
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    verdict TEXT,
                    severity TEXT,
                    timestamp TEXT,
                    ticket_id TEXT,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (run_id, step_id)
                );
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    step_id TEXT,
                    severity TEXT,
                    status TEXT,
                    ticket_id TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    step_id TEXT,
                    severity TEXT,
                    status TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    step_id TEXT,
                    ticket_id TEXT,
                    incident_id TEXT,
                    timestamp TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    step_id TEXT,
                    type TEXT,
                    timestamp TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_verdicts_run ON verdicts(run_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_run ON tickets(run_id);
                CREATE INDEX IF NOT EXISTS idx_incidents_run ON incidents(run_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_run ON audit_logs(run_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidence(run_id);
                """
            )
            connection.commit()

            if self._table_count(connection, "runs") == 0:
                self._seed_database(connection)

    def _seed_database(self, connection: sqlite3.Connection) -> None:
        self._seed_runs(connection)
        self._seed_checklist_steps(connection)
        self._seed_verdicts(connection)
        self._seed_incidents(connection)
        self._seed_tickets(connection)
        self._seed_audit_logs(connection)
        self._seed_evidence(connection)
        connection.commit()

    def _seed_runs(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("runs.json"):
            connection.execute(
                "INSERT INTO runs(run_id, payload) VALUES(?, ?)",
                [self._normalize(record.get("run_id")), json.dumps(record)],
            )

    def _seed_checklist_steps(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("checklist_steps.json"):
            connection.execute(
                """
                INSERT INTO checklist_steps(run_id, step_id, sequence_number, payload)
                VALUES(?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    record.get("sequence_number"),
                    json.dumps(record),
                ],
            )

    def _seed_verdicts(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("verdicts.json"):
            connection.execute(
                """
                INSERT INTO verdicts(run_id, step_id, verdict, severity, timestamp, ticket_id, payload)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    self._normalize(record.get("verdict")),
                    self._normalize(record.get("severity")),
                    str(record.get("timestamp") or ""),
                    self._normalize(record.get("ticket_id")),
                    json.dumps(record),
                ],
            )

    def _seed_incidents(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("incidents.json"):
            connection.execute(
                """
                INSERT INTO incidents(incident_id, run_id, step_id, severity, status, ticket_id, payload)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("incident_id")),
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    self._normalize(record.get("severity")),
                    self._normalize(record.get("status")),
                    self._normalize(record.get("ticket_id")),
                    json.dumps(record),
                ],
            )

    def _seed_tickets(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("tickets.json"):
            connection.execute(
                """
                INSERT INTO tickets(ticket_id, run_id, step_id, severity, status, payload)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("ticket_id")),
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    self._normalize(record.get("severity")),
                    self._normalize(record.get("status")),
                    json.dumps(record),
                ],
            )

    def _seed_audit_logs(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("audit_logs.json"):
            connection.execute(
                """
                INSERT INTO audit_logs(run_id, step_id, ticket_id, incident_id, timestamp, payload)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    self._normalize(record.get("ticket_id")),
                    self._normalize(record.get("incident_id")),
                    str(record.get("timestamp") or ""),
                    json.dumps(record),
                ],
            )

    def _seed_evidence(self, connection: sqlite3.Connection) -> None:
        for record in self._load_records("evidence.json"):
            connection.execute(
                """
                INSERT INTO evidence(evidence_id, run_id, step_id, type, timestamp, start_time, end_time, payload)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    self._normalize(record.get("evidence_id")),
                    self._normalize(record.get("run_id")),
                    self._normalize(record.get("step_id")),
                    str(record.get("type") or "").lower(),
                    str(record.get("timestamp") or ""),
                    str(record.get("start_time") or ""),
                    str(record.get("end_time") or ""),
                    json.dumps(record),
                ],
            )

    def _query_evidence(
        self,
        evidence_type: str,
        run_id: str,
        step_id: str | None,
        timestamp: str | None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT payload FROM evidence WHERE run_id = ? AND type = ?"
        params: list[Any] = [self._normalize(run_id), evidence_type.lower()]
        if step_id is not None:
            sql += " AND step_id = ?"
            params.append(self._normalize(step_id))
        if timestamp is not None:
            sql += " AND (? IN (UPPER(COALESCE(timestamp, '')), UPPER(COALESCE(start_time, '')), UPPER(COALESCE(end_time, ''))))"
            params.append(self._normalize(timestamp))
        return self._fetch_payloads(sql, params)

    def _fetch_payloads(self, sql: str, params: list[Any]) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._decode_payload(row[0]) for row in rows]

    def _fetch_one(self, sql: str, params: list[Any]) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(sql, params).fetchone()
        if row is None:
            return None
        return self._decode_payload(row[0])

    def _table_count(self, connection: sqlite3.Connection, table_name: str) -> int:
        row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0]) if row else 0

    def _load_records(self, filename: str) -> list[dict[str, Any]]:
        path = self._data_dir / filename
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        return [record for record in payload if isinstance(record, dict)]

    def _decode_payload(self, payload: str) -> dict[str, Any]:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _normalize(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().upper()
