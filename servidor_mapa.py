#!/usr/bin/env python3
"""
Servidor local del Mapa de Calor de Opciones
Usa las APIs de la plataforma original y evita problemas de CORS.
"""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import webbrowser
import threading
import time

BASE_API = "https://scientists-pal-knife-chicago.trycloudflare.com"
PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))

ACTIVOS_PERMITIDOS = ["SPX", "NDX", "QQQ", "SPY", "IWM", "AAPL", "NVDA", "TSLA", "COIN", "BTC", "ETH", "VIX"]

YAHOO_MAP = {
    "NDX": "QQQ", "QQQ": "QQQ", "SPX": "^GSPC", "SPY": "SPY", "IWM": "IWM",
    "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "COIN": "COIN",
    "BTC": "BTC-USD", "ETH": "ETH-USD", "VIX": "^VIX",
}


def fetch_api(path):
    url = BASE_API + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MapaCalorLocal/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), {}
    except Exception as e:
        return 502, json.dumps({"error": str(e)}).encode(), {}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Historial de precios (Yahoo, gratis) para el gráfico
        if path == "/api/precios":
            qs = parse_qs(parsed.query)
            sym = (qs.get("s") or ["QQQ"])[0].upper()
            ysym = YAHOO_MAP.get(sym, sym)
            range_ = (qs.get("r") or ["3mo"])[0]
            interval = (qs.get("i") or ["1d"])[0]
            yurl = (
                "https://query1.finance.yahoo.com/v8/finance/chart/"
                + urllib.request.quote(ysym)
                + f"?interval={interval}&range={range_}"
            )
            try:
                req = urllib.request.Request(yurl, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    raw = json.loads(resp.read().decode())
                result = (raw.get("chart") or {}).get("result") or [None]
                result = result[0]
                if not result:
                    raise ValueError("sin datos")
                ts = result.get("timestamp") or []
                quote = (result.get("indicators") or {}).get("quote") or [{}]
                closes = (quote[0] or {}).get("close") or []
                bars = []
                for t, c in zip(ts, closes):
                    if c is None:
                        continue
                    bars.append({"time": int(t), "value": float(c)})
                body = json.dumps({"s": sym, "yahoo": ysym, "bars": bars}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # Proxy de las APIs originales
        if path.startswith("/api/"):
            qs = parsed.query
            status, body, _ = fetch_api(path + ("?" + qs if qs else ""))
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        # Lista de activos permitidos
        if path == "/activos":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ACTIVOS_PERMITIDOS).encode())
            return

        # Dashboard principal
        if path in ("/", "/index.html", "/mapa"):
            self.path = "/mapa_calor_live.html"
            return super().do_GET()

        return super().do_GET()

    def log_message(self, format, *args):
        msg = format % args
        if "/api/" in msg or "activos" in msg:
            print(f"  {msg}")


def main():
    html_path = os.path.join(DIR, "mapa_calor_live.html")
    if not os.path.exists(html_path):
        print("ERROR: No se encontró mapa_calor_live.html")
        return

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print("=" * 55)
    print("  MAPA DE CALOR · OPCIONES  (datos reales)")
    print("=" * 55)
    print(f"  Abre en tu navegador:  {url}")
    print(f"  Activos: {', '.join(ACTIVOS_PERMITIDOS)}")
    print("  Ctrl+C para detener")
    print("=" * 55)

    def open_browser():
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
