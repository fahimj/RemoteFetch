#!/usr/bin/env python3
import asyncio
import json
import base64
import os
import time
import logging
from pathlib import Path

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv('CLIENT_ID', 'client_1')
# use ws://localhost:8080 for local server, use wss://remotefetch-490044025500.us-west1.run.app to connect a deployed server in GCP cloud run
SERVER_URL = os.getenv('SERVER_URL', 'wss://remotefetch-490044025500.us-west1.run.app')
FILE_PATH = os.getenv('FILE_PATH', '$HOME/file_to_download.txt')
CHUNK_SIZE = 1024 * 1024


def get_file_path():
    path = FILE_PATH.replace('$HOME', str(Path.home()))
    return Path(path)


async def send_file(ws):
    file_path = get_file_path()

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        await ws.send(json.dumps({'type': 'error', 'msg': 'File not found'}))
        return

    logger.info(f"Sending {file_path}")

    chunk_num = 0
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            await ws.send(json.dumps({
                'num': chunk_num,
                'data': base64.b64encode(chunk).decode('utf-8')
            }))
            chunk_num += 1

    await ws.send(json.dumps({'type': 'complete'}))
    logger.info(f"Sent {chunk_num} chunks")


async def run():
    url = f"{SERVER_URL}/ws/{CLIENT_ID}"

    while True:
        try:
            async with websockets.connect(url, compression="deflate") as ws:
                logger.info(f"Connected as {CLIENT_ID}")
                async for message in ws:
                    data = json.loads(message)
                    if data.get('type') == 'download':
                        await send_file(ws)
        except Exception as e:
            logger.error(f"Error: {e}")

        await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(run())
