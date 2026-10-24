#!/usr/bin/env python3
"""南京 Apple Store 线下取货 · iPhone Duo 库存监控（本地服务）.

浏览器跨域限制，网页不能直接请求 apple.com.cn，所以由这个小服务代为查询
Apple 官网的「门店取货」接口，并提供监控网页。只用 Python 标准库。

    python3 apple-monitor/server.py          # 浏览器打开 http://localhost:8765
    python3 apple-monitor/server.py --demo   # 演示模式：随机模拟有货，用来测试提醒
"""
import argparse
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent

API = "https://www.apple.com.cn/shop/fulfillment-messages"
BUY_URL = "https://www.apple.com.cn/shop/buy-iphone/iphone-duo"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

# 国行 iPhone Duo 全部型号，取自 apple.com.cn 购买页
MODELS = [
    {"part": "MK2M4CH/A", "capacity": "256GB", "color": "星光白色", "price": 15999},
    {"part": "MK2N4CH/A", "capacity": "256GB", "color": "夜空色", "price": 15999},
    {"part": "MK2P4CH/A", "capacity": "512GB", "color": "星光白色", "price": 17999},
    {"part": "MK2Q4CH/A", "capacity": "512GB", "color": "夜空色", "price": 17999},
    {"part": "MK2T4CH/A", "capacity": "1TB", "color": "星光白色", "price": 21499},
    {"part": "MK2U4CH/A", "capacity": "1TB", "color": "夜空色", "price": 21499},
    {"part": "MK2V4CH/A", "capacity": "2TB", "color": "星光白色", "price": 26499},
    {"part": "MK2W4CH/A", "capacity": "2TB", "color": "夜空色", "price": 26499},
]

# 南京的 Apple Store（apple.com.cn/retail/storelist）；新开门店会按城市名自动加入
CITY = "南京"
STORES = {"R493": "新街口", "R703": "玄武湖", "R643": "虹悦城"}
DEFAULT_LOCATION = "江苏 南京 玄武区"

# 多个网页同时打开时共用一次查询，避免频繁请求 Apple
CACHE_SECONDS = 10


def query_apple(parts, location):
    """查询一批型号在 location 附近门店的取货情况，返回 Apple 原始门店列表."""
    params = [("pl", "true"), ("mts.0", "regular")]
    params += [(f"parts.{i}", p) for i, p in enumerate(parts)]
    params.append(("location", location))
    req = Request(f"{API}?{urlencode(params)}", headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": BUY_URL,
    })
    try:
        with urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="ignore")
    except HTTPError as e:
        if e.code == 541:
            raise RuntimeError("Apple 拒绝了查询（541），可能是请求太频繁或当前网络被限制，稍后会自动重试")
        raise RuntimeError(f"Apple 接口返回 HTTP {e.code}")
    except URLError as e:
        raise RuntimeError(f"连接 Apple 失败：{e.reason}")
    try:
        msg = json.loads(raw)["body"]["content"]["pickupMessage"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("Apple 返回的不是库存数据，接口可能有变化")
    if msg.get("errorMessage"):
        raise RuntimeError(f"Apple：{msg['errorMessage']}")
    return msg.get("stores") or []


def fetch_stock(location):
    parts = [m["part"] for m in MODELS]
    stores = {}

    def merge(raw_stores):
        for s in raw_stores:
            num = s.get("storeNumber")
            if num not in STORES and CITY not in (s.get("city") or ""):
                continue
            entry = stores.setdefault(num, {
                "number": num, "name": STORES.get(num) or s.get("storeName") or num, "avail": {}})
            for part, info in (s.get("partsAvailability") or {}).items():
                entry["avail"][part] = {
                    "status": info.get("pickupDisplay") or "unknown",
                    "quote": info.get("pickupSearchQuote") or "",
                }

    raw = query_apple(parts, location)
    merge(raw)
    # 一次查全部型号；Apple 若漏掉某些型号，再逐个补查
    seen = {p for s in raw for p in (s.get("partsAvailability") or {})}
    for p in parts:
        if p not in seen:
            merge(query_apple([p], location))

    if not stores:
        raise RuntimeError(f"附近门店里没有南京的 Apple Store，请检查 --location（当前：{location}）")
    order = list(STORES)
    return sorted(stores.values(), key=lambda s: order.index(s["number"]) if s["number"] in order else 99)


def demo_stock():
    return [{"number": num, "name": name, "avail": {
        m["part"]: ({"status": "available", "quote": "今天"} if random.random() < 0.08
                    else {"status": "unavailable", "quote": "暂无供应"})
        for m in MODELS}} for num, name in STORES.items()]


class Monitor:
    def __init__(self, location, demo):
        self.location, self.demo = location, demo
        self.lock = threading.Lock()
        self.cached_at, self.cached = 0.0, None

    def snapshot(self):
        with self.lock:
            if self.cached and time.time() - self.cached_at < CACHE_SECONDS:
                return self.cached
            result = {"ok": True, "demo": self.demo, "buyUrl": BUY_URL, "models": MODELS}
            try:
                result["stores"] = demo_stock() if self.demo else fetch_stock(self.location)
            except RuntimeError as e:
                result = {"ok": False, "error": str(e)}
            result["checkedAt"] = int(time.time() * 1000)
            self.cached_at, self.cached = time.time(), result
            return result


def make_handler(monitor):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                self.send(200, "text/html; charset=utf-8", (HERE / "index.html").read_bytes())
            elif path == "/api/stock":
                data = monitor.snapshot()
                self.send(200 if data["ok"] else 502, "application/json; charset=utf-8",
                          json.dumps(data, ensure_ascii=False).encode("utf-8"))
            else:
                self.send(404, "text/plain; charset=utf-8", b"not found")

        def send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass  # 每 20 秒一次的轮询日志没有意义

    return Handler


def main():
    ap = argparse.ArgumentParser(description="南京 Apple Store iPhone Duo 取货库存监控")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1", help="设为 0.0.0.0 可让同一局域网的手机访问")
    ap.add_argument("--location", default=DEFAULT_LOCATION, help="查询位置（省 市 区）")
    ap.add_argument("--demo", action="store_true", help="演示模式：随机模拟库存，不请求 Apple")
    args = ap.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), make_handler(Monitor(args.location, args.demo)))
    shown = "localhost" if args.host in ("127.0.0.1", "0.0.0.0") else args.host
    print(f"监控页面：http://{shown}:{args.port}" + ("（演示模式）" if args.demo else ""))
    print("按 Ctrl+C 退出")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
