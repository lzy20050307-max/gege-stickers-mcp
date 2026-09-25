# 哥哥表情包：遠端 MCP 服務

這是現有 `gege-stickers` 外掛要使用的遠端服務，不是另一個 ChatGPT 外掛。從 jsDelivr package API 取得 `lzy20050307-max/gege-stickers@main` 的檔案清單，避免共用主機的 GitHub API 匿名請求限額；`show_sticker` 驗證檔名後，保留原本 MCP `image` content block，並連結一個最小化 MCP Apps 圖片元件，讓支援 UI resource 的 ChatGPT 用戶端直接呈現圖片。

## 部署

將本資料夾的 `Dockerfile`、`server.py`、`stickers_core.py`、`sticker-widget.html` 與 `README.md` 部署到支援 Docker 的常駐 HTTPS 服務。容器使用環境變數 `PORT`（預設 8000），提供 `/health` 和 `/mcp`。服務必須能向 `data.jsdelivr.com` 和 `cdn.jsdelivr.net` 發出 HTTPS 請求。

先確認 `https://<你的網域>/health` 回傳 `{"status":"ok"}`，再用 MCP Inspector 以 Streamable HTTP 連接 `https://<你的網域>/mcp`，確認 `resources/list`、`resources/read`、`list_stickers` 與 `show_sticker`。部署後在 ChatGPT 外掛詳情頁重新整理連線／工具中繼資料，再開新聊天測試圖片元件。

這個服務只讀取公開圖片，沒有登入或寫入操作。任何知道 endpoint 的人都可以呼叫這兩個工具；若要限制存取，需要另行設計驗證。
