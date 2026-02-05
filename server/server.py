#!/usr/bin/env python3
import base64
from flask import Flask, jsonify, Response, stream_with_context
from flask_sock import Sock
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# Store: {client_id: websocket}
clients = {}
# Store: {client_id: list of chunks}
downloads = {}


@sock.route('/ws/<client_id>')
def websocket_handler(ws, client_id):
    """Handle WebSocket - client_id is in URL path. Flask-Sock passes (ws, route_args)."""
    clients[client_id] = ws
    logger.info(f"Client {client_id} connected ({len(clients)} total)")
    
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
            
            data = json.loads(msg)
            
            # Store chunks for active downloads
            if client_id in downloads:
                downloads[client_id].append(data)
    
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]
        logger.info(f"Client {client_id} disconnected")


@app.route('/api/clients')
def list_clients():
    keys = list(clients.keys())
    return jsonify({'count': len(keys), 'clients': keys})


@app.route('/api/download/<client_id>')
def download_file(client_id):
    if client_id not in clients:
        return jsonify({'error': 'Client not connected'}), 404
    
    import time
    try:
        downloads[client_id] = []
        clients[client_id].send(json.dumps({'type': 'download'}))
        
        # Wait for first chunk (or complete) so we can return 408 if no data
        timeout = 60
        start = time.time()
        while time.time() - start < timeout:
            if downloads[client_id]:
                break
            time.sleep(0.1)
        else:
            if client_id in downloads:
                del downloads[client_id]
            return jsonify({'error': 'No data received'}), 408
        
        def generate():
            start_ts = time.time()
            try:
                while True:
                    if downloads[client_id]:
                        chunk = downloads[client_id].pop(0)
                        if chunk.get('type') == 'complete':
                            break
                        data = base64.b64decode(chunk['data'])
                        logger.info(f"Chunk {chunk['num']}: {len(data)} bytes")
                        yield data
                        start_ts = time.time()
                    else:
                        if time.time() - start_ts > timeout:
                            break
                        time.sleep(0.05)
            finally:
                if client_id in downloads:
                    del downloads[client_id]
        
        return Response(
            stream_with_context(generate()),
            mimetype='application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename=file_{client_id}.txt'}
        )
    
    except Exception as e:
        if client_id in downloads:
            del downloads[client_id]
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
