# ============================================
# EALPR Cloud Deployment — Railway / Render
# ============================================
FROM python:3.11-slim

# System dependencies for OpenCV headless + PaddleOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy deployment requirements first (Docker layer caching)
COPY requirements-deploy.txt .

# Pin numpy FIRST to prevent version wars between torch/opencv/paddle
RUN pip install --no-cache-dir numpy==1.26.4

# Install CPU-only PyTorch (saves ~1.5GB vs GPU version)
RUN pip install --no-cache-dir \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY models/ ./models/

# Railway assigns a dynamic PORT — default to 8000 if not set
ENV PORT=8000

# Start the server using Railway's dynamic PORT
CMD python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
