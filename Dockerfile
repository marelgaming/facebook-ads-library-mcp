# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY requirements-remote.txt .
RUN pip install --no-cache-dir -r requirements-remote.txt

COPY src ./src
COPY remote_server.py .

ENTRYPOINT ["python", "remote_server.py"]
