"""
FastAPI Backend for EALPR System
"""
import os, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import cv2, numpy as np

from src.pipeline import process_image, process_base64_image
from src.severity import get_all_severities, get_categories
from src.database import (
    get_recent_scans, 
    get_scan_count, 
    file_report, 
    get_reports_by_plate, 
    get_recent_reports, 
    get_hotspot_plates, 
    confirm_report,
    get_plate_severity
)

app = FastAPI(title="Aman | أمان", description="Egyptian License Plate Recognition & Community Safety Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

FRONTEND_DIR = PROJECT_ROOT / "frontend"

class FrameRequest(BaseModel):
    image: str
    confidence_threshold: float = 0.25

class ReportRequest(BaseModel):
    plate_text: str = Field(..., min_length=1, max_length=20)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    reported_by: Optional[str] = Field("anonymous", max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    governorate: Optional[str] = Field(None, max_length=50)

@app.get("/api/health")
async def health_check(): return {"status": "healthy"}

@app.post("/api/detect")
async def detect_plate(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"): raise HTTPException(status_code=400, detail="Must be image")
    img = cv2.imdecode(np.frombuffer(await file.read(), np.uint8), cv2.IMREAD_COLOR)
    return JSONResponse(process_image(img))

@app.post("/api/detect-frame")
async def detect_frame(req: FrameRequest):
    return JSONResponse(process_base64_image(req.image, req.confidence_threshold))

@app.get("/history")
async def get_history(limit: int = 50):
    """
    Retrieve Scan History
    
    Fetches the most recent license plate scans from the database.
    Query limit defaults to 50, maximum of 200.
    """
    if limit > 200:
        limit = 200
        
    try:
        scans = get_recent_scans(limit=limit)
        return {"scans": scans, "count": len(scans)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """
    Retrieve Database Statistics
    
    Fetches the total number of scans tracked and the timestamp of the last active scan.
    """
    try:
        total = get_scan_count()
        recent = get_recent_scans(limit=1)
        last_scan = recent[0]["timestamp"] if recent else None
        
        return {
            "total_scans": total,
            "last_scan": last_scan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/report")
async def create_report(request: ReportRequest):
    """
    File a Report
    
    Submits a community danger report for a specific license plate.
    """
    try:
        report_id = file_report(
            plate_text=request.plate_text,
            category=request.category,
            description=request.description or "",
            reported_by=request.reported_by or "anonymous",
            latitude=request.latitude,
            longitude=request.longitude,
            governorate=request.governorate
        )
        return {
            "report_id": report_id,
            "plate_text": request.plate_text,
            "message": "Report filed successfully"
        }
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/plate/{plate_text}/severity")
async def get_plate_severity_endpoint(plate_text: str):
    """
    Live Plate Danger Level
    
    Retrieves the aggregate real-time danger severity assigned to a plate text profile dynamically.
    """
    try:
        plate_text_upper = plate_text.upper()
        return get_plate_severity(plate_text_upper)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/plate/{plate_text}")
async def get_plate_reports(plate_text: str):
    """
    Get Reports by Plate
    
    Retrieves all active reports filed against a specific license plate.
    """
    try:
        plate_text_upper = plate_text.upper()
        reports = get_reports_by_plate(plate_text_upper)
        return {"plate_text": plate_text_upper, "reports": reports, "report_count": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/hotspots")
async def get_hotspots(min_reports: int = 2):
    """
    Get Danger Hotspots
    
    Retrieves license plates that have been reported multiple times. Used for generating community heatmaps.
    """
    try:
        hotspots = get_hotspot_plates(min_reports)
        return {"hotspots": hotspots, "total": len(hotspots)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/report/{report_id}/confirm")
async def confirm_plate_report(report_id: int):
    """
    Confirm a Report
    
    Increments the confirmation count of an existing report.
    """
    try:
        confirmed = confirm_report(report_id)
        return {"confirmed": confirmed, "report_id": report_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/config")
async def get_config():
    """
    Get Application Config
    
    Returns static structural information driving the application layout and enumerations.
    """
    return {
        "severities": get_all_severities(),
        "categories": get_categories(),
        "app_name": "Aman",
        "app_name_ar": "أمان",
        "version": "1.0.0"
    }

@app.get("/")
async def serve_frontend():
    idx = FRONTEND_DIR / "index.html"
    return FileResponse(str(idx)) if idx.exists() else JSONResponse({"message": "Frontend not found"})

@app.get("/sw.js")
async def serve_sw():
    idx = FRONTEND_DIR / "sw.js"
    return FileResponse(str(idx)) if idx.exists() else JSONResponse({"message": "Service worker not found"})

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

if __name__ == "__main__":
    import uvicorn
    import sys
    if "--tunnel" in sys.argv:
        from pyngrok import ngrok
        public_url = ngrok.connect(8000)
        print("\n" + "="*80)
        print(f"🌍 SECURE GLOBAL LINK (Open this on your phone): {public_url.public_url}")
        print("="*80 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
