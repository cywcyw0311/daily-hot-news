# 每日热点 Top 10

手机优化的每日新闻聚合页，每天早上 7 点（北京时间）自动更新：

- **国内热点 Top 10**：今日头条热榜
- **国际热点 Top 10**：联合早报国际版

## 本地预览

```bash
python3 scripts/fetch_news.py   # 生成 data/news.json
python3 -m http.server 8000     # 浏览器打开 http://localhost:8000
```

## 部署

推送到 GitHub 后，在仓库 Settings → Pages 中选择 **Deploy from a branch**、
分支 `main`、目录 `/ (root)` 即可发布。`.github/workflows/update-news.yml`
会每天定时抓取并提交最新的 `data/news.json`。
