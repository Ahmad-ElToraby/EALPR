# أمان | Aman
## Egyptian License Plate Recognition & Community Safety Platform

### Quick Start
Run start.bat — opens server and ngrok tunnel simultaneously.
Access locally: http://localhost:8000
Access remotely: check http://127.0.0.1:4040 for the ngrok URL

### API Endpoints
- `GET /api/health` - Check if the API is running correctly.
- `POST /api/detect` - Process an uploaded image file for license plates.
- `POST /api/detect-frame` - Process a base64 encoded image frame for immediate detection.
- `GET /history` - Retrieve previously recorded plate scans efficiently.
- `GET /stats` - Fetch database telemetry showing total volume and latest tracking timestamp.
- `POST /report` - Open a community danger report tracking a specific license plate.
- `GET /plate/{plate_text}` - Query the entire history of danger reports filed against a string pattern.
- `GET /hotspots` - Identify multiple-report occurrences driving community heatmap data.
- `POST /report/{report_id}/confirm` - Add verification tracking to a previous report.
- `GET /config` - Sync frontend application styling limits and enumeration translations.
- `GET /` - Retrieve the compiled mobile frontend UI application payload.
- `GET /sw.js` - Initialize background service worker cache routines.

### Governorate Classifier
The classifier uses a deterministic three-step algorithm:
1. If the plate has 3 digits → Cairo
2. If the plate has 2 letters → Giza  
3. If the plate has 4 digits + 3 letters:
   - Check first 2 letters against prefix table (T_ = Suez Canal/Sinai, C_ = Upper Egypt, G_ = Western Frontier)
   - If no prefix match, check final letter against suffix table (S = Alexandria, M = Monufia, R = Sharqia, etc.)

All 27 governorates are covered. No heuristics. No external database queries.

### Tech Stack
FastAPI, PaddleOCR, YOLOv8, SQLite, Vanilla JS PWA

### Version History
v1.0.0 — Initial release
v0.3.0 — Community features
v0.2.0 — Database persistence  
v0.1.0 — Core ALPR fixes
