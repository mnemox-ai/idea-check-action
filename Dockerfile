FROM python:3.11-slim

WORKDIR /app

# Install deps (pin versions if you want)
RUN pip install --no-cache-dir idea-reality-mcp httpx

# Copy action code
COPY entrypoint.py /app/entrypoint.py

# GitHub Actions passes inputs as env vars to container automatically
ENTRYPOINT ["python", "/app/entrypoint.py"]
