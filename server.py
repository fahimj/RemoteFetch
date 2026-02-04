#!/usr/bin/env python3
import asyncio
import base64
from flask import Flask, jsonify, Response
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
    
    try:
        # Initialize download
        downloads[client_id] = []
        
        # Request file
        clients[client_id].send(json.dumps({'type': 'download'}))
        
        # Collect chunks (simple polling with timeout)
        import time
        timeout = 60
        start = time.time()
        file_data = bytearray()
        
        while time.time() - start < timeout:
            if downloads[client_id]:
                chunk = downloads[client_id].pop(0)
                
                if chunk.get('type') == 'complete':
                    break
                
                # Decode chunk
                chunk_bytes = base64.b64decode(chunk['data'])
                file_data.extend(chunk_bytes)
                logger.info(f"Chunk {chunk['num']}: {len(chunk_bytes)} bytes")
            else:
                time.sleep(0.1)  # Wait for data
        
        # Cleanup
        del downloads[client_id]
        
        if not file_data:
            return jsonify({'error': 'No data received'}), 408
        
        logger.info(f"Download complete: {len(file_data)} bytes")
        
        return Response(
            bytes(file_data),
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