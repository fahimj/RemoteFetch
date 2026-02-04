#!/usr/bin/env python3
"""
Simple CLI for the file download system
"""
import requests
import sys

SERVER = "http://localhost:8080"


def list_clients():
    """List connected clients"""
    r = requests.get(f"{SERVER}/api/clients")
    data = r.json()
    print(f"\nConnected clients ({data['count']}):")
    for client in data['clients']:
        print(f"  - {client}")


def download_file(client_id, output='downloaded.txt'):
    """Download file from client"""
    print(f"Downloading from {client_id}...")
    
    r = requests.get(f"{SERVER}/api/download/{client_id}")
    
    if r.status_code == 200:
        with open(output, 'wb') as f:
            f.write(r.content)
        print(f"✓ Downloaded: {output} ({len(r.content):,} bytes)")
    else:
        print(f"✗ Error: {r.json().get('error')}")
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
