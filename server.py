#!/usr/bin/env python3
"""Stateless Streamable HTTP MCP endpoint at /mcp."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from stickers_core import TOOLS, call

PROTOCOL = "2025-03-26"
MAX_REQUEST = 64 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "GegeStickersMCP/0.3"

    def respond(self, status, value=None):
        data = b"" if value is None else json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("MCP-Protocol-Version", PROTOCOL)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.respond(200, {"status": "ok"})
        if self.path == "/mcp":
            return self.respond(405, {"error": "This stateless MCP endpoint uses POST"})
        return self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/mcp":
            return self.respond(404, {"error": "Not found"})
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > MAX_REQUEST:
            return self.respond(413, {"error": "Invalid request size"})
        try:
            req = json.loads(self.rfile.read(length))
            if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
                raise ValueError("Expected JSON-RPC 2.0 object")
        except (ValueError, UnicodeDecodeError) as exc:
            return self.respond(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}})

        if "id" not in req:
            return self.respond(202)
        method = req.get("method")
        if method == "initialize":
            result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "gege-stickers", "version": "0.3.0"}, "instructions": "Use list_stickers to select a real filename, then show_sticker to return its image."}
        elif method == "tools/list":
            result = {"tools": [{**tool, "annotations": {"readOnlyHint": True, "openWorldHint": False}} for tool in TOOLS]}
        elif method == "tools/call":
            params = req.get("params") or {}
            try:
                result = call(params.get("name"), params.get("arguments") or {})
            except Exception as exc:
                result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        elif method == "ping":
            result = {}
        else:
            return self.respond(200, {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "Method not found"}})
        return self.respond(200, {"jsonrpc": "2.0", "id": req["id"], "result": result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
