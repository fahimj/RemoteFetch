# RemoteFetch

This codebase demonstrates a Python system that lets **on-premise clients** (e.g. restaurants) without public IPs share their local files via a **cloud-hosted server**. On-premise clients stay behind NAT/firewalls and are not reachable from the internet; they become reachable by maintaining a persistent **WebSocket** connection to the server. The server then relays file requests from admins (REST API or CLI) to the right client and streams the file back.

## Architecture

- **Restaurant Clients**: Behind NAT, maintain WebSocket connection to server
- **Cloud Server**: Receives WebSocket connections + exposes REST API
- **Admin Users**: Use API or CLI to trigger downloads from specific restaurants

To support large file transfers (e.g. 100 MB+), a key architectural choice is **streaming**: the server streams the download response using chunked transfer encoding instead of buffering the whole file, avoiding platform response-size limits (e.g. Cloud Run’s 32 MB non-streaming limit) and keeping memory use bounded.

## Project Structure

```
.
├── server/              # Server (deploy to cloud)
│   ├── server.py
│   ├── Dockerfile
│   ├── .dockerignore
│   └── requirements.txt
├── client/              # Client & CLI (on-premise / admin)
│   ├── client.py        # Restaurant client
│   ├── cli.py           # Admin CLI tool
│   └── requirements.txt
├── LICENSE
└── README.md
```

## Setup

### Server (Cloud)

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
# Runs on http://0.0.0.0:8080
```

To build and run with Docker:
```bash
cd server
docker build -t remotefetch-server .
docker run -p 8080:8080 remotefetch-server
```

**Cloud Run:** The server uses the eventlet worker to avoid protocol errors behind the proxy.

**Deployed instance:** The server is deployed on GCP Cloud Run. To access it, use: `https://remotefetch-490044025500.us-west1.run.app`

### Restaurant Client (On-Premise)

Before running the client, ensure there is a file at the path `$HOME/file_to_download.txt`

The client connects to the server at **`wss://remotefetch-490044025500.us-west1.run.app`** by default. Override with `SERVER_URL` for a different server.

```bash
cd client
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
CLIENT_ID=restaurant_sf python client.py
# Connects to server, waits for download requests
```

### Admin/User (Laptop/Desktop)

The CLI and examples below use the deployed server: **`https://remotefetch-490044025500.us-west1.run.app`**

```bash
cd client
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Option 1: CLI
python cli.py list                              # See connected restaurants
python cli.py download restaurant_sf menu.txt   # Download file

# Option 2: API
curl https://remotefetch-490044025500.us-west1.run.app/api/clients             # List restaurants
curl https://remotefetch-490044025500.us-west1.run.app/api/download/restaurant_sf -o menu.txt
```

## API

- **GET /api/clients** — `{"count": N, "clients": ["client_id", ...]}`
- **GET /api/download/<client_id>** — binary file, or `404` / `408` / `500` JSON error
