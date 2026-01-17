from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json

from database import SessionLocal, init_db, ProtocolState

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
init_db()

# Default Template Data (Logic from original index.html)
DEFAULT_STATE = {
    "metadata": {"client": "", "date": "", "tech": "", "ticket": ""},
    "backup": [
        {"id": "conf", "label": "Konfigurations-Backup", "method": "Export DSM (.dss)", "ref": "", "done": False},
        {"id": "hyper", "label": "Disaster Recovery", "method": "Hyper Backup Prüfung", "ref": "Letzter Stand: Heute", "done": False},
        {"id": "snap", "label": "Dateisystem-Snapshots", "method": "Btrfs-Snapshots (Docker)", "ref": "", "done": False},
        {"id": "db", "label": "Datenbank-Sicherung", "method": "SQL-Dump (All)", "ref": "", "done": False}
    ],
    "host": [
        {"id": "dsm", "name": "DSM OS (Host)", "old": "", "new": "", "reason": "Security Fix / Update", "done": False},
        {"id": "drive", "name": "Synology Drive", "old": "", "new": "", "reason": "Stabilität", "done": False},
        {"id": "hyperb", "name": "Hyper Backup", "old": "", "new": "", "reason": "Optimierung", "done": False},
        {"id": "active", "name": "Active Backup", "old": "", "new": "", "reason": "Kompatibilität", "done": False},
        {"id": "sec", "name": "Security Advisor", "old": "-", "new": "-", "reason": "System-Scan", "done": False}
    ],
    "docker": [
        {"id": "nc", "name": "Nextcloud", "old": "", "new": "", "reason": "PHP-Stack Update", "done": False},
        {"id": "auth", "name": "Authentik", "old": "", "new": "", "reason": "Blueprint Updates", "done": False},
        {"id": "vault", "name": "Vaultwarden", "old": "", "new": "", "reason": "Web-Vault Check", "done": False},
        {"id": "n8n", "name": "n8n", "old": "", "new": "", "reason": "NodeJS Version", "done": False},
        {"id": "pg", "name": "PostgreSQL", "old": "", "new": "", "reason": "Persistenz Check", "done": False}
    ],
    "qaHost": [
        {"id": "q_dsm", "name": "DSM Dashboard", "scen": "Ressourcen & Logs", "expect": "Stabil, keine Fehler", "res": False},
        {"id": "q_file", "name": "Dateidienste", "scen": "SMB / Drive-Client", "expect": "Sync erfolgreich", "res": False},
        {"id": "q_bak", "name": "Backup-Dienste", "scen": "Manueller Trigger", "expect": "Replikation OK", "res": False}
    ],
    "qaApp": [
        {"id": "q_nc", "name": "Nextcloud", "scen": "Web-GUI & App", "expect": "Login & Vorschau OK", "res": False},
        {"id": "q_au", "name": "Authentik", "scen": "SSO / Flow", "expect": "Login via OIDC", "res": False},
        {"id": "q_vw", "name": "Vaultwarden", "scen": "Vault-Sync", "expect": "Datenabgleich OK", "res": False},
        {"id": "q_n8n", "name": "n8n", "scen": "Workflow-Test", "expect": "Execution Core-WF", "res": False}
    ]
}

class StateUpdate(BaseModel):
    data: Dict[str, Any]

@app.get("/api/state")
def get_state(db: Session = Depends(get_db)):
    state = db.query(ProtocolState).filter(ProtocolState.id == 1).first()
    if not state:
        # Initialize if empty
        state = ProtocolState(id=1, data=DEFAULT_STATE)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state.data

@app.post("/api/state")
def update_state(update: StateUpdate, db: Session = Depends(get_db)):
    state = db.query(ProtocolState).filter(ProtocolState.id == 1).first()
    if not state:
        state = ProtocolState(id=1, data=update.data)
        db.add(state)
    else:
        state.data = update.data
    
    db.commit()
    return {"status": "ok"}

@app.delete("/api/state")
def reset_state(db: Session = Depends(get_db)):
    state = db.query(ProtocolState).filter(ProtocolState.id == 1).first()
    if state:
        state.data = DEFAULT_STATE
        db.commit()
    return DEFAULT_STATE

# Serve Static Files (Frontend)
# We assume index.html is in the same directory as main.py for this simple setup,
# or we can move it to a 'static' folder. 
# Plan: Serve index.html at root, and map other static assets if needed.

@app.get("/")
async def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found"}

