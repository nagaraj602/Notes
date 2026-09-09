# ==========================================
# Stage 1: Build & Dependencies
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system build dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
	git \
    && rm -rf /var/lib/apt/lists/*
	
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Final Minimal Runtime Image
# ==========================================
FROM python:3.11-slim AS runtime
WORKDIR /app
# Install git and ca-certificates for repo cloning and HTTPS

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*                                   
# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH 
ENV PYTHONUNBUFFERED=1

# Copy application source code
COPY app/ /app/app/

# Create data directory for notes storage
RUN mkdir -p /app/data/notes  

# Environment variable defaults
ENV REPO_URL="https://github.com/nagaraj602/Notes.git"
ENV REPO_BRANCH="main"
ENV AUTO_SYNC_INTERVAL_MINUTES=5
ENV NOTES_DIR="/app/data/notes"
ENV PORT=8000

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
  
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]