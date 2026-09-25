#!/usr/bin/env python3
"""Stateless Streamable HTTP MCP endpoint at /mcp."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from stickers_core import TOOLS, call

PROTOCOL = "2025-03-26"
MAX_REQUEST = 64 * 1024
SERVER_VERSION = "0.4.0"
RESOURCE_URI = "ui://widget/gege-sticker.html"
RESOURCE_MIME_TYPE = "text/html;profile=mcp-app"
WIDGET_HTML = Path(__file__).with_name("sticker-widget.html").read_text(encoding="utf-8")


def list_resources():
    return {
        "resources": [
            {
                "uri": RESOURCE_URI,
                "name": "gege-sticker-widget",
                "title": "哥哥表情包",
                "description": "在 ChatGPT 對話中顯示 show_sticker 回傳的表情包圖片。",
                "mimeType": RESOURCE_MIME_TYPE,
            }
        ]
    }


def read_resource(uri):
    if uri != RESOURCE_URI:
        raise ValueError("Unknown resource URI")
    csp = {
        "connectDomains": [],
        "resourceDomains": ["https://cdn.jsdelivr.net"],
    }
    return {
        "contents": [
            {
                "uri": RESOURCE_URI,
                "mimeType": RESOURCE_MIME_TYPE,
                "text": WIDGET_HTML,
                "_meta": {
                    "ui": {"prefersBorder": False, "csp": csp},
                    "openai/widgetDescription": "顯示使用者指定的哥哥表情包圖片。",
                    "openai/widgetPrefersBorder": False,
                    "openai/widgetCSP": {
                        "connect_domains": [],
                        "resource_domains": ["https://cdn.jsdelivr.net"],
                    },
                },
            }
        ]
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "GegeStickersMCP/0.4"

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
            result = {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}, "resources": {"listChanged": False}},
                "serverInfo": {"name": "gege-stickers", "version": SERVER_VERSION},
                "instructions": "Use list_stickers to select a real filename, then show_sticker to return its image.",
            }
        elif method == "tools/list":
            result = {"tools": [{**tool, "annotations": {"readOnlyHint": True, "openWorldHint": False}} for tool in TOOLS]}
        elif method == "tools/call":
            params = req.get("params") or {}
            try:
                result = call(params.get("name"), params.get("arguments") or {})
            except Exception as exc:
                result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        elif method == "resources/list":
            result = list_resources()
        elif method == "resources/read":
            params = req.get("params") or {}
            try:
                result = read_resource(params.get("uri"))
            except Exception as exc:
                return self.respond(200, {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32002, "message": str(exc)}})
        elif method == "ping":
            result = {}
        else:
            return self.respond(200, {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "Method not found"}})
        return self.respond(200, {"jsonrpc": "2.0", "id": req["id"], "result": result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
