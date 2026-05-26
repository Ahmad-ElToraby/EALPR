---
title: Aman - أمان
emoji: 🚗
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# 🚗 Aman (أمان) — Egyptian License Plate Recognition & Community Safety Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8m-Ultralytics-00FFFF?logo=yolo)](https://docs.ultralytics.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Deployed-2496ED?logo=docker&logoColor=white)](https://hub.docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hugging Face](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face-FFD21E)](https://huggingface.co/spaces/T3NT4CLE/Aman)

A full-stack AI-powered mobile web application that detects and reads Egyptian license plates in real time, classifies vehicle types by plate color, identifies governorates from plate codes, and enables community danger reporting — all through a bilingual Arabic/English Progressive Web App.

**🔗 [Live Demo on Hugging Face Spaces](https://huggingface.co/spaces/T3NT4CLE/Aman)**

---

## 📊 Key Metrics

<table>
<tr>
<td align="center"><b>🎯 Detection Precision</b><br><br><h1>99.7%</h1></td>
<td align="center"><b>🔍 Detection Recall</b><br><br><h1>98.8%</h1></td>
<td align="center"><b>📈 mAP@50</b><br><br><h1>99.5%</h1></td>
<td align="center"><b>📉 mAP@50-95</b><br><br><h1>92.4%</h1></td>
</tr>
</table>

| Detail | Value |
|---|---|
| **Dataset** | 3,547 images (2,920 train / 313 val / 314 test) |
| **Training** | 100 epochs on NVIDIA RTX 4070 (~3.9 hours) |
| **Model** | YOLOv8m — 25.9M parameters, COCO pretrained |
| **Optimizer** | AdamW with AMP (mixed precision) |

---

## ✨ Features

- 🔎 **Real-Time Plate Detection** — YOLOv8m with 99.5% mAP, focuses on the largest plate in frame
- 🔤 **Arabic OCR** — PaddleOCR with multi-strategy enhancement (CLAHE, Otsu, Adaptive Thresholding)
- 🎨 **Vehicle Type Classification** — K-Means clustering on HSV color space (Private, Taxi, Police, Diplomatic, etc.)
- 🗺️ **27 Governorate Identification** — Deterministic prefix/suffix algorithm on plate codes
- 🌐 **Bilingual PWA** — Full Arabic/English toggle with RTL support, installable on mobile
- 🚨 **Community Danger Reporting** — File reports with severity levels, community confirmations
- 📷 **Camera Zoom Control** — Hardware-level 1x–5x optical zoom via MediaStream API
- 🃏 **Sharable Warning Cards** — Canvas-generated images for social media sharing
- 🐳 **Docker Deployment** — Containerized for Hugging Face Spaces with CI/CD
- 🔄 **Multi-Strategy OCR Pipeline** — Tries 3 enhancement methods per plate, picks highest-confidence result

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Detection** | YOLOv8m (Ultralytics) |
| **OCR Engine** | PaddleOCR with Arabic post-processing |
| **Image Enhancement** | CLAHE + Sharpening + Denoising (OpenCV) |
| **Color Classification** | K-Means Clustering on HSV color space |
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | Progressive Web App (HTML/CSS/JS) — bilingual |
| **Database** | SQLite |
| **Deployment** | Hugging Face Spaces via Docker |
| **Training Hardware** | NVIDIA RTX 4070 (CUDA) |

---

## ⚙️ How It Works

The system uses a **3-stage hierarchical pipeline**:

```
📸 Input Image
    │
    ▼
┌─────────────────────┐
│  Stage 1: DETECTION  │  YOLOv8m detects license plate bounding boxes
│  (plate_detector.pt) │  Focuses on largest plate (closest to camera)
└────────┬────────────┘
         │ crop
         ▼
┌─────────────────────┐
│  Stage 2: OCR        │  Multi-strategy enhancement pipeline:
│  (PaddleOCR)         │  • CLAHE + Sharpen + Denoise
└────────┬────────────┘  • Otsu Binary Threshold
         │               • Adaptive Gaussian Threshold
         │               → Best confidence wins
         ▼
┌─────────────────────┐
│  Stage 3: CLASSIFY   │  • K-Means HSV → Vehicle Type
│  (Rules + K-Means)   │  • Prefix/Suffix → Governorate
└─────────────────────┘
```

---

## 🗺️ Governorate Classifier

The classifier uses a **deterministic three-step algorithm** — no ML, no external DB lookups:

1. **3 digits** → **Cairo** (القاهرة)
2. **2 letters** → **Giza** (الجيزة)
3. **4 digits + 3 letters** →
   - Check first 2 letters against **prefix table**:
     - `T_` = Suez Canal / Sinai zone (Damietta, Port Said, Ismailia, Suez, Red Sea, North/South Sinai)
     - `C_` = Upper Egypt (Qena, Luxor, Aswan)
     - `G_` = Western Frontier (Matrouh, New Valley)
   - If no prefix match → check **final letter** against suffix table (S=Alexandria, M=Monufia, R=Sharqia, D=Dakahlia, etc.)

All **27 governorates** are covered with 100% deterministic mapping.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/detect` | Upload image file for plate detection |
| `POST` | `/api/detect-frame` | Process base64 camera frame |
| `GET` | `/history` | Retrieve recent plate scan records |
| `GET` | `/stats` | Database telemetry (total scans, latest timestamp) |
| `POST` | `/report` | File a community danger report |
| `GET` | `/plate/{plate_text}` | Get all reports for a specific plate |
| `GET` | `/plate/{plate_text}/severity` | Get aggregated threat level |
| `GET` | `/hotspots` | Multi-report plates driving community heatmap |
| `POST` | `/report/{id}/confirm` | Community verification of a report |
| `GET` | `/config` | Frontend config (categories, severity levels) |

---

## 🚀 Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Ahmad-ElToraby/EALPR.git
cd EALPR

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Or on Windows, simply run:
start.bat
```

Access at **http://localhost:8000**

---

## 🐳 Docker Deployment

```bash
docker build -t aman .
docker run -p 7860:7860 aman
```

---

## 📁 Project Structure

```
EALPR/
├── src/
│   ├── main.py              # FastAPI server
│   ├── pipeline.py          # Detection + OCR + Classification pipeline
│   ├── ocr_engine.py        # PaddleOCR wrapper with Arabic processing
│   ├── feature_extractor.py # K-Means HSV vehicle type classifier
│   ├── classifier.py        # Governorate classifier
│   ├── database.py          # SQLite data layer
│   └── severity.py          # Threat severity configuration
├── frontend/
│   ├── index.html           # PWA shell
│   ├── app.js               # Application logic
│   ├── index.css            # Styles
│   ├── manifest.json        # PWA manifest
│   └── sw.js                # Service worker
├── models/
│   └── plate_detector.pt    # Trained YOLOv8m weights
├── dataset/
│   └── data.yaml            # Dataset configuration
├── Dockerfile               # Production container
├── requirements.txt         # Python dependencies
└── start.bat                # Windows quick start
```

---

## 📜 Version History

| Version | Changes |
|---|---|
| **v1.0.0** | Full release — multi-strategy OCR, camera zoom, manual fallback UI, Docker deployment |
| **v0.3.0** | Community features — reporting, severity levels, hotspots, warning cards |
| **v0.2.0** | Database persistence — SQLite scan history, stats API |
| **v0.1.0** | Core ALPR — YOLOv8m detection, PaddleOCR, governorate classification |

---

## 👤 Author

**Ahmad ElToraby** — Computer Engineering, BUE + LSBU

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ahmad%20ElToraby-0A66C2?logo=linkedin)](https://www.linkedin.com/in/ahmad-eltoraby/)
[![GitHub](https://img.shields.io/badge/GitHub-Ahmad--ElToraby-181717?logo=github)](https://github.com/Ahmad-ElToraby)

---

<p align="center">Built with ❤️ in Cairo, Egypt 🇪🇬</p>
