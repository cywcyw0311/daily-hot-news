#!/usr/bin/env python3
"""每日新闻抓取脚本：国内 Top10（今日头条热榜）+ 国际 Top10（联合早报国际版）.

输出 data/news.json，由 GitHub Actions 每天定时运行。
单个源失败不影响另一个源；全部失败时保留旧文件并退出非零。
"""
import json
import re
import html as htmlmod
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
      "Mobile/15E148 Safari/604.1")

BEIJING = timezone(timedelta(hours=8))


def get(url, timeout=25):
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def fetch_domestic():
    """今日头条热榜 Top10."""
    raw = get("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    data = json.loads(raw)["data"]
    items = []
    for it in data[:10]:
        title = (it.get("Title") or "").strip()
        url = (it.get("Url") or "").strip()
        if not title or not url:
            continue
        items.append({
            "title": title,
            "url": url,
            "hot": it.get("HotValue"),
            "label": (it.get("LabelDesc") or "").strip() or None,
        })
    return items


def fetch_world():
    """联合早报国际版 Top10."""
    h = get("https://www.zaobao.com.sg/news/world")
    pats = re.findall(r'<a[^>]*href="(/news/world/story\d+-\d+)"[^>]*>(.*?)</a>', h, re.S)
    items, seen = [], set()
    for href, inner in pats:
        if href in seen:
            continue
        text = htmlmod.unescape(re.sub(r"<[^>]+>", "", inner))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 8:
            continue
        seen.add(href)
        items.append({
            "title": text,
            "url": "https://www.zaobao.com.sg" + href,
            "hot": None,
            "label": None,
        })
        if len(items) >= 10:
            break
    return items


def main():
    out_path = "data/news.json"
    domestic, world = [], []
    errors = []

    try:
        domestic = fetch_domestic()
        print(f"domestic: {len(domestic)} items")
    except Exception as e:  # noqa: BLE001
        errors.append(f"domestic: {e}")

    try:
        world = fetch_world()
        print(f"world: {len(world)} items")
    except Exception as e:  # noqa: BLE001
        errors.append(f"world: {e}")

    if not domestic and not world:
        print("ERROR: all sources failed:", "; ".join(errors), file=sys.stderr)
        sys.exit(1)

    payload = {
        "updated_at": datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M"),
        "domestic": domestic,
        "world": world,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"wrote {out_path}")
    if errors:
        print("warnings:", "; ".join(errors), file=sys.stderr)


if __name__ == "__main__":
    main()
