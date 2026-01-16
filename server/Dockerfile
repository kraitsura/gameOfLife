FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck and uv for package management
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies using uv (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run application using uv with optimized settings
CMD ["uv", "run", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--loop", "uvloop", \
     "--timeout-keep-alive", "75", \
     "--timeout-graceful-shutdown", "30"]

EXPOSE 8000