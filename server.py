import asyncio
import json
import logging
from typing import Callable, Optional

class TCPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 27121,
                 callback: Optional[Callable[[dict], None]] = None,
                 *, backlog: int = 100, recv_buffer: int = 4096):
        self.host = host
        self.port = port
        self.callback = callback
        self.backlog = backlog
        self.recv_buffer = recv_buffer
        self._server: Optional[asyncio.AbstractServer] = None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        logging.info(f"Connection from {addr}")
        data = bytearray()
        try:
            while not reader.at_eof():
                chunk = await reader.read(self.recv_buffer)
                if not chunk:
                    break
                data.extend(chunk)
            text = data.decode(errors="ignore")
            if "\r\n\r\n" in text:
                _, body = text.split("\r\n\r\n", 1)
            else:
                body = text
            payload = json.loads(body)
            logging.info(f"Received JSON payload: {payload!r}")
            if self.callback:
                asyncio.create_task(self._run_callback(payload))
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON from {addr}: {e}")
        except Exception as e:
            logging.error(f"Error handling {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logging.info(f"Connection closed: {addr}")

    async def _run_callback(self, payload: dict):
        try:
            result = self.callback(payload)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logging.error(f"Error in callback: {e}")

    async def start(self):
        if self._server:
            return
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port, backlog=self.backlog
        )
        addr = self._server.sockets[0].getsockname()
        logging.info(f"TCPServer listening on {addr}")

    async def stop(self):
        if not self._server:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        logging.info("TCPServer has stopped")

    async def serve_forever(self):
        await self.start()
        await asyncio.Event().wait()
