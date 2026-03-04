from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3, json, os
from datetime import datetime

app = FastAPI(title="Server Provisioning API")

# --- CORS: restrict to your internal domain in production ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://srv-req.persol.net"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "provisioning.db"

# ── Models ──────────────────────────────────────────────────
class Subdomain(BaseModel):
    name: str
    description: Optional[str] = ""

class ServerSpec(BaseModel):
    hostname: Optional[str] = ""
    environment: Optional[str] = ""
    region: Optional[str] = ""
    os: str
    ram: str
    cpu: str
    storage: str
    ssl: bool = False
    firewall: bool = False
    monitoring: bool = False
    autoBackup: Optional[str] = "None"
    subdomains: List[Subdomain] = []
    notes: Optional[str] = ""

class ProvisioningRequest(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = ""
    project: str
    priority: str
    justification: Optional[str] = ""
    servers: List[ServerSpec]

# ── DB Setup ─────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            status      TEXT DEFAULT 'Pending',
            name        TEXT,
            email       TEXT,
            department  TEXT,
            project     TEXT,
            priority    TEXT,
            justification TEXT,
            servers_json TEXT
        )
    """)
    con.commit()
    con.close()

init_db()

# ── Routes ───────────────────────────────────────────────────
@app.post("/api/requests", status_code=201)
def submit_request(req: ProvisioningRequest):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO requests
            (submitted_at, name, email, department, project, priority, justification, servers_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        req.name, req.email, req.department,
        req.project, req.priority, req.justification,
        json.dumps([s.dict() for s in req.servers])
    ))
    rid = cur.lastrowid
    con.commit()
    con.close()
    return {"message": "Request submitted successfully.", "request_id": rid}


@app.get("/api/requests")
def list_requests(status: Optional[str] = None):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    if status:
        rows = cur.execute("SELECT * FROM requests WHERE status=? ORDER BY submitted_at DESC", (status,)).fetchall()
    else:
        rows = cur.execute("SELECT * FROM requests ORDER BY submitted_at DESC").fetchall()
    con.close()
    results = []
    for r in rows:
        d = dict(r)
        d["servers"] = json.loads(d.pop("servers_json"))
        results.append(d)
    return results


@app.get("/api/requests/{request_id}")
def get_request(request_id: int):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    row = cur.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found.")
    d = dict(row)
    d["servers"] = json.loads(d.pop("servers_json"))
    return d


@app.patch("/api/requests/{request_id}/status")
def update_status(request_id: int, status: str):
    allowed = {"Pending", "Approved", "Rejected", "Provisioning", "Completed"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE requests SET status=? WHERE id=?", (status, request_id))
    if cur.rowcount == 0:
        con.close()
        raise HTTPException(status_code=404, detail="Request not found.")
    con.commit()
    con.close()
    return {"message": f"Status updated to '{status}'.", "request_id": request_id}


@app.delete("/api/requests/{request_id}")
def delete_request(request_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM requests WHERE id=?", (request_id,))
    if cur.rowcount == 0:
        con.close()
        raise HTTPException(status_code=404, detail="Request not found.")
    con.commit()
    con.close()
    return {"message": "Request deleted.", "request_id": request_id}
