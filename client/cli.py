#!/usr/bin/env python3
"""
Simple CLI for the file download system
"""
import requests
import sys

SERVER = "https://remotefetch-490044025500.us-west1.run.app"


def list_clients():
    """List connected clients"""
    r = requests.get(f"{SERVER}/api/clients")
    data = r.json()
    print(f"\nConnected clients ({data['count']}):")
    for client in data['clients']:
        print(f"  - {client}")


def download_file(client_id, output='downloaded.txt'):
    """Download file from client (streamed for large files)"""
    print(f"Downloading from {client_id}...")
    
    r = requests.get(f"{SERVER}/api/download/{client_id}", stream=True)
    
    if r.status_code == 200:
        size = 0
        with open(output, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
        print(f"✓ Downloaded: {output} ({size:,} bytes)")
    else:
        try:
            msg = r.json().get('error', r.text or r.reason)
        except Exception:
            msg = r.text or r.reason or f"HTTP {r.status_code}"
        print(f"✗ Error: {msg}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py list")
        print("  python cli.py download <client_id> [output_file]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        list_clients()
    elif cmd == 'download' and len(sys.argv) >= 3:
        client_id = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else 'downloaded.txt'
        download_file(client_id, output)
    else:
        print("Invalid command")
        sys.exit(1)
