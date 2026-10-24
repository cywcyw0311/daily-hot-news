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

`apple-monitor/index.html` 是一个独立的小工具：每 20 秒查询一次 Apple 官网，看南京三家
Apple Store（新街口、玄武湖、虹悦城）能否门店取货 iPhone Duo，8 个型号都查
（256GB / 512GB / 1TB / 2TB × 星光白色 / 夜空色）。有货时会高亮对应型号并响铃，
直到点「知道了」才停。

Apple 官网不允许其他网站读取库存，所以监控以书签的形式在 apple.com.cn 页面里运行：

1. 打开 `apple-monitor/index.html`（GitHub Pages 上是 `/apple-monitor/`），把「Duo 南京库存」按钮拖到书签栏
2. 打开 <https://www.apple.com.cn/shop/buy-iphone/iphone-duo>
3. 点这个书签，监控面板会盖在页面上开始工作；点一下面板顶部的蓝条启用声音

页面要一直开着，电脑不要休眠。页面上有「演示」按钮，可以先试听提醒音。
