from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
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
        {"id": "conf", "label": "Konfigurations-Backup", "method": "Export DSM (.dss)", "ref": "", "status": "pending"},
        {"id": "hyper", "label": "Disaster Recovery", "method": "Hyper Backup Prüfung", "ref": "Letzter Stand: Heute", "status": "pending"},
        {"id": "snap", "label": "Dateisystem-Snapshots", "method": "Btrfs-Snapshots (Docker)", "ref": "", "status": "pending"},
        {"id": "db", "label": "Datenbank-Sicherung", "method": "SQL-Dump (All)", "ref": "", "status": "pending"}
    ],
    "host": [
        {"id": "dsm", "name": "DSM OS (Host)", "old": "", "new": "", "reason": "Security Fix / Update", "rel_notes": "", "status": "pending"},
        {"id": "drive", "name": "Synology Drive", "old": "", "new": "", "reason": "Stabilität", "rel_notes": "", "status": "pending"},
        {"id": "hyperb", "name": "Hyper Backup", "old": "", "new": "", "reason": "Optimierung", "rel_notes": "", "status": "pending"},
        {"id": "active", "name": "Active Backup", "old": "", "new": "", "reason": "Kompatibilität", "rel_notes": "", "status": "pending"},
        {"id": "sec", "name": "Security Advisor", "old": "-", "new": "-", "reason": "System-Scan", "rel_notes": "", "status": "pending"}
    ],
    "docker": [
        {"id": "nc", "name": "Nextcloud", "old": "", "new": "", "reason": "PHP-Stack Update", "rel_notes": "", "status": "pending"},
        {"id": "auth", "name": "Authentik", "old": "", "new": "", "reason": "Blueprint Updates", "rel_notes": "", "status": "pending"},
        {"id": "vault", "name": "Vaultwarden", "old": "", "new": "", "reason": "Web-Vault Check", "rel_notes": "", "status": "pending"},
        {"id": "n8n", "name": "n8n", "old": "", "new": "", "reason": "NodeJS Version", "rel_notes": "", "status": "pending"},
        {"id": "pg", "name": "PostgreSQL", "old": "", "new": "", "reason": "Persistenz Check", "rel_notes": "", "status": "pending"}
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

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Drawing
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from io import BytesIO

@app.get("/api/report/pdf")
def generate_pdf(db: Session = Depends(get_db)):
    state = db.query(ProtocolState).filter(ProtocolState.id == 1).first()
    data = state.data if state else DEFAULT_STATE
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    h2_style = styles['Heading2']
    h3_style = styles['Heading3']
    normal_style = styles['BodyText']

    # --- Title & Metadata ---
    elements.append(Paragraph("Patchday Protokoll", title_style))
    elements.append(Spacer(1, 12))
    
    meta_data = [
        ["Mandant:", data['metadata'].get('client', '-')],
        ["Datum:", data['metadata'].get('date', '-')],
        ["Techniker:", data['metadata'].get('tech', '-')],
        ["Ticket:", data['metadata'].get('ticket', '-')]
    ]
    t_meta = Table(meta_data, colWidths=[100, 300])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 24))

    # --- Charts ---
    # Progress Chart
    completed = 0
    in_progress = 0
    total = 0
    
    # Helper to count status
    def check_status(item):
        s = item.get('status', 'pending')
        # Compatibility with old boolean done
        if item.get('done') is True: s = 'done'
        return s

    for cat in ['backup', 'host', 'docker']:
        for item in data[cat]:
            s = check_status(item)
            if s == 'done': completed += 1
            elif s == 'wip': in_progress += 1
            total += 1
    
    # QA
    for cat in ['qaHost', 'qaApp']:
        for item in data[cat]:
            if item.get('res'): completed += 1
            total += 1

    remaining = total - completed - in_progress
    
    # Draw Pie
    d = Drawing(400, 150)
    pc = Pie()
    pc.x = 100
    pc.y = 25
    pc.data = [completed, in_progress, remaining]
    pc.labels = [f'Done ({completed})', f'WIP ({in_progress})', f'Open ({remaining})']
    pc.slices[0].fillColor = colors.limegreen
    pc.slices[1].fillColor = colors.yellow
    pc.slices[2].fillColor = colors.lightgrey
    d.add(pc)
    elements.append(d)
    elements.append(Spacer(1, 12))

    # --- 1. Backup ---
    elements.append(Paragraph("1. Quality Assurance: Backup", h2_style))
    backup_data = [["Status", "Checkpoint", "Methode", "Bemerkung"]]
    for item in data['backup']:
        s = check_status(item)
        status_text = "OK" if s == 'done' else ("WIP" if s == 'wip' else "OFFEN")
        backup_data.append([status_text, item.get('label',''), item.get('method',''), item.get('ref','')])
    
    t_backup = Table(backup_data, colWidths=[50, 150, 150, 100])
    t_backup.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(t_backup)
    elements.append(Spacer(1, 18))

    # --- 2. Infrastructure & Docker ---
    elements.append(Paragraph("2. Updates (Infrastruktur & Container)", h2_style))
    update_data = [["Status", "Komponente", "Alt", "Neu", "Grund", "Ref"]]
    
    for item in data['host']:
         s = check_status(item)
         status_text = "OK" if s == 'done' else ("WIP" if s == 'wip' else "OFFEN")
         update_data.append([status_text, item.get('name',''), item.get('old',''), item.get('new',''), item.get('reason',''), item.get('rel_notes','')])
         
    for item in data['docker']:
         s = check_status(item)
         status_text = "OK" if s == 'done' else ("WIP" if s == 'wip' else "OFFEN")
         update_data.append([status_text, item.get('name',''), item.get('old',''), item.get('new',''), item.get('reason',''), item.get('rel_notes','')])

    t_updates = Table(update_data, colWidths=[40, 100, 60, 60, 100, 90])
    t_updates.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8), # Reduce font size to fit
    ]))
    elements.append(t_updates)
    elements.append(Spacer(1, 18))

    # --- 3. QA ---
    elements.append(Paragraph("3. Funktionstests (UAT)", h2_style))
    qa_data = [["Ergebnis", "Test", "Szenario"]]
    for item in data['qaHost']:
        res = "OK" if item.get('res') else "FAIL"
        qa_data.append([res, item.get('name',''), item.get('scen','')])
    for item in data['qaApp']:
        res = "OK" if item.get('res') else "FAIL"
        qa_data.append([res, item.get('name',''), item.get('scen','')])

    t_qa = Table(qa_data, colWidths=[60, 200, 200])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(t_qa)
    elements.append(Spacer(1, 18))
    
    # --- Remarks ---
    elements.append(Paragraph("Bemerkungen", h2_style))
    remarks = data['metadata'].get('remarks', 'Keine besonderen Vorkommnisse.')
    elements.append(Paragraph(remarks, normal_style))

    doc.build(elements)
    buffer.seek(0)
    
    filename = f"PatchProtokoll_{data['metadata'].get('client', 'Client')}_{data['metadata'].get('date', 'Date')}.pdf"
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


# Serve Static Files (Frontend)
# We assume index.html is in the same directory as main.py for this simple setup,
# or we can move it to a 'static' folder. 
# Plan: Serve index.html at root, and map other static assets if needed.

@app.get("/")
async def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found"}

