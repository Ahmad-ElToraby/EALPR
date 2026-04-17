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

# Install CPU-only PyTorch first (saves ~1.5GB vs GPU version)
RUN pip install --no-cache-dir \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY models/ ./models/

# Expose the port Railway/Render will route to
EXPOSE 8000

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Start the server (no --tunnel needed in cloud!)
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
