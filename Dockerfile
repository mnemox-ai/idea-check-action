FROM python:3.11-slim

COPY entrypoint.py /entrypoint.py

RUN pip install --no-cache-dir idea-reality-mcp httpx

ENTRYPOINT ["python", "/entrypoint.py"]
