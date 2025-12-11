"""
web_watcher.py

Local WebSocket server that receives active tab URLs from a browser extension.
Each message is expected to be JSON: {"url": "...", "title": "..."}.

Events are pushed into a Queue for the main thread to handle:
    {"type": "web_foreground", "url": "...", "title": "..."}

Requires: pip install websockets
"""

from __future__ import annotations
import asyncio
import json
import threading
from queue import Queue
from typing import Dict, Any

import websockets


class WebWatcher:
    """Runs a local WebSocket server that receives active tab URLs."""

    def __init__(self, event_queue: Queue, host: str = "127.0.0.1", port: int = 8765):
        self.event_queue = event_queue
        self.host = host
        self.port = port
        self._thread: threading.Thread | None = None
        self._stop_flag = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_flag = True

    def _run_loop(self) -> None:
        asyncio.run(self._async_main())

    async def _async_main(self) -> None:
        async def handler(websocket):
            async for message in websocket:
                try:
                    data: Dict[str, Any] = json.loads(message)
                    url = data.get("url", "")
                    title = data.get("title", "")
                    self.event_queue.put(
                        {
                            "type": "web_foreground",
                            "url": url,
                            "title": title,
                        }
                    )
                except Exception:
                    # Ignore malformed messages
                    continue

        async with websockets.serve(handler, self.host, self.port):
            while not self._stop_flag:
                await asyncio.sleep(0.2)
