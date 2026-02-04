FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Cloud Run injects the PORT environment variable
ENV PORT=8080

# Use gevent worker for WebSocket support
# --workers 1: Required because app uses in-memory state (clients/downloads dicts)
# --timeout 0: Prevents WebSocket connection timeouts
CMD exec gunicorn --bind :$PORT --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --timeout 0 server:app
