# 哥哥表情包：遠端 MCP 服務

這是現有 `gege-stickers` 外掛要使用的遠端服務，不是另一個 ChatGPT 外掛。`list_stickers` 從 jsDelivr package API 取得 `lzy20050307-max/gege-stickers@main` 的最新圖片清單，避免共用主機的 GitHub API 匿名請求限額；`show_sticker` 驗證檔名後，只回傳對應的 jsDelivr 公開圖片 URL。

## 部署

將本資料夾的 `Dockerfile`、`server.py`、`stickers_core.py` 與 `README.md` 部署到支援 Docker 的常駐 HTTPS 服務。容器使用環境變數 `PORT`（預設 8000），提供 `/health` 和 `/mcp`。服務只需向 `data.jsdelivr.com` 取得最新檔案清單；`show_sticker` 不會下載圖片或轉換 Base64。

先確認 `https://<你的網域>/health` 回傳 `{"status":"ok"}`，再用 MCP Inspector 以 Streamable HTTP 連接 `https://<你的網域>/mcp`，測試 `list_stickers`、`show_sticker`（含不存在的檔名）。`show_sticker("5972_我要親嘴.jpg")` 應只回傳 `https://cdn.jsdelivr.net/gh/lzy20050307-max/gege-stickers@main/5972_我要親嘴.jpg`。

這個服務只讀取公開圖片，沒有登入或寫入操作。任何知道 endpoint 的人都可以呼叫這兩個工具；若要限制存取，需要另行設計驗證。
