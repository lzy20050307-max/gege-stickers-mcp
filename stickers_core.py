#!/usr/bin/env python3
"""Sticker catalog and image content for the remote MCP service."""
import base64
import json
import sys
import urllib.parse
import urllib.request

REPO = "lzy20050307-max/gege-stickers"
MIMES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif"}
MAX_IMAGE = 5 * 1024 * 1024


def get(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "gege-stickers-mcp/0.2"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read(MAX_IMAGE + 1)


def catalog():
    # GitHub's anonymous API is rate limited on shared hosting IPs. The
    # jsDelivr package API provides the CDN's current file tree without it.
    branch = "main"
    metadata = json.loads(get(f"https://data.jsdelivr.com/v1/package/gh/{REPO}@{branch}"))
    paths = []

    def collect(nodes, prefix=""):
        for item in nodes:
            path = prefix + item["name"]
            if item["type"] == "directory":
                collect(item.get("files", []), path + "/")
            elif item["type"] == "file" and any(path.lower().endswith(ext) for ext in MIMES):
                paths.append(path)

    collect(metadata["files"])
    paths.sort()
    return branch, paths


TOOLS = [
    {"name": "list_stickers", "description": "取得公開 GitHub 倉庫中最新的表情包圖片路徑清單。", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "show_sticker", "description": "依實際存在的相對路徑或唯一檔名，從 jsDelivr 取回表情包，直接以圖片內容回傳。", "inputSchema": {"type": "object", "properties": {"filename": {"type": "string", "description": "圖片檔名或倉庫內相對路徑"}}, "required": ["filename"], "additionalProperties": False}},
]


def call(name, args):
    if name not in {tool["name"] for tool in TOOLS}:
        raise ValueError("Unknown tool")
    branch, paths = catalog()
    if name == "list_stickers":
        return {"content": [{"type": "text", "text": json.dumps({"repository": REPO, "branch": branch, "count": len(paths), "files": paths}, ensure_ascii=False)}]}
    filename = args.get("filename")
    if not isinstance(filename, str) or not filename:
        raise ValueError("filename 必須是非空字串。")
    matches = [p for p in paths if p == filename]
    if not matches:
        matches = [p for p in paths if p.rsplit("/", 1)[-1] == filename]
    if len(matches) != 1:
        raise ValueError(f"找不到唯一圖片；符合的路徑：{matches}")
    path = matches[0]
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    url = f"https://cdn.jsdelivr.net/gh/{REPO}@{urllib.parse.quote(branch, safe='')}/{encoded}"
    data = get(url, "image/*")
    if not data or len(data) > MAX_IMAGE:
        raise ValueError("圖片為空或超過 5 MiB。")
    mime = next(mime for ext, mime in MIMES.items() if path.lower().endswith(ext))
    return {"content": [{"type": "text", "text": json.dumps({"filename": path, "url": url}, ensure_ascii=False)}, {"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": mime}]}

