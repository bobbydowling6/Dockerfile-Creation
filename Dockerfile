FROM python:3.11-slim

WORKDIR /workspace

# Prevent Python from buffering stdout/stderr (ensures instant log visibility)
ENV PYTHONUNBUFFERED=1

# Install minimal C/C++ compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

COPY app/requirements.txt .

# Upgrade packaging tools to handle modern wheels smoothly
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install CPU-only PyTorch first
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining application dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app

WORKDIR /workspace/app

EXPOSE 8000

# Start Uvicorn pointing directly to rag-api.py's app instance
CMD ["uvicorn", "rag-api:app", "--host", "0.0.0.0", "--port", "8000"]