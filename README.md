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

## iPhone Duo 南京取货库存监控

`apple-monitor/` 是一个独立的小工具：每 20 秒查询一次 Apple 官网，看南京三家
Apple Store（新街口、玄武湖、虹悦城）能否门店取货 iPhone Duo，8 个型号都查
（256GB / 512GB / 1TB / 2TB × 星光白色 / 夜空色）。有货时会高亮对应型号并响铃，
直到点「知道了」才停。

Apple 官网不允许网页跨域查询，所以要在自己电脑上运行一个本地服务（不需要装依赖）：

```bash
python3 apple-monitor/server.py          # 浏览器打开 http://localhost:8765
python3 apple-monitor/server.py --demo   # 演示模式，随机模拟有货，用来试听提醒音
```

- 打开页面后点一下顶部蓝色横条，启用声音（浏览器要求）和桌面通知
- 想用同一 Wi-Fi 下的手机查看：加 `--host 0.0.0.0`，手机访问 `http://电脑IP:8765`
- 页面要一直开着，电脑不要休眠
