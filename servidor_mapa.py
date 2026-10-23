#!/usr/bin/env python3
"""
Mapa de Calor · Opciones — Plan B (sin API propia)
Fuente: CBOE delayed quotes (OI + gamma oficiales, ~15 min).
Calcula: Max Pain, Call/Put Wall, GEX por strike, Gamma Flip.
"""

import json
import re
import time
import threading
import webbrowser
import urllib.request
from collections import defaultdict
from datetime import datetime, date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import os

PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))

CBOE_MAP = {
    "NDX": "QQQ",
    "QQQ": "QQQ",
    "SPX": "_SPX",
    "SPY": "SPY",
    "IWM": "IWM",
    "AAPL": "AAPL",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "COIN": "COIN",
    "VIX": "_VIX",
}

YAHOO_CHART = {
    "NDX": "QQQ", "QQQ": "QQQ", "SPX": "^GSPC", "SPY": "SPY", "IWM": "IWM",
    "AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "COIN": "COIN",
    "BTC": "BTC-USD", "ETH": "ETH-USD", "VIX": "^VIX",
}

ACTIVOS = list(CBOE_MAP.keys()) + ["BTC", "ETH"]
OCC_RE = re.compile(r"^([A-Z0-9._]+)(\d{6})([CP])(\d{8})$")
_cache = {}
CACHE_TTL = 90


def http_json(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (MapaCalor/2.0)", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def fetch_cboe_chain(cboe_sym):
    url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{quote(cboe_sym)}.json"
    return http_json(url)


def parse_expiry(ymd):
    try:
        return datetime.strptime(ymd, "%y%m%d").date()
    except Exception:
        return None


def calc_max_pain(by_strike, spot):
    if not by_strike:
        return None
    keys = sorted(by_strike.keys())
    cands = [k for k in keys if abs(k - spot) / max(spot, 1e-9) <= 0.20]
    if len(cands) < 5:
        cands = keys

    def pain(K):
        t = 0.0
        for k, v in by_strike.items():
            t += v["oi_c"] * max(0.0, K - k)
            t += v["oi_p"] * max(0.0, k - K)
        return t

    return min(cands, key=pain)


def calc_gamma_flip(strike_gex):
    if len(strike_gex) < 2:
        return None
    cum = 0.0
    prev_k = strike_gex[0][0]
    prev_cum = 0.0
    for k, g in strike_gex:
        prev_cum = cum
        cum += g
        if prev_cum != 0 and (prev_cum > 0) != (cum > 0):
            denom = abs(prev_cum) + abs(cum)
            if denom == 0:
                return k
            t = abs(prev_cum) / denom
            return prev_k + (k - prev_k) * t
        prev_k = k
    best = min(strike_gex, key=lambda x: abs(x[1]))
    return best[0]


def build_from_cboe(symbol, horizon_days=30):
    if symbol in ("BTC", "ETH"):
        return {
            "error": f"{symbol} no tiene cadena equity en CBOE. Usa QQQ/SPY.",
            "id": symbol,
        }

    cboe_sym = CBOE_MAP.get(symbol)
    if not cboe_sym:
        return {"error": f"Símbolo no soportado: {symbol}", "id": symbol}

    raw = fetch_cboe_chain(cboe_sym)
    data = raw.get("data") or raw
    spot = float(data.get("current_price") or 0)
    options = data.get("options") or []
    if not options or spot <= 0:
        return {"error": "Sin opciones o sin precio", "id": symbol}

    today = date.today()
    horizon = int(horizon_days) if horizon_days else 30
    by_strike = defaultdict(lambda: {"oi_c": 0.0, "oi_p": 0.0, "gex": 0.0})
    nearest_exp = None

    for o in options:
        name = (o.get("option") or "").replace(" ", "")
        m = OCC_RE.match(name)
        if not m:
            continue
        _, ymd, cp, kraw = m.groups()
        exp = parse_expiry(ymd)
        if not exp:
            continue
        dte = (exp - today).days
        if dte < 0 or dte > horizon:
            continue
        if nearest_exp is None or exp < nearest_exp:
            nearest_exp = exp

        strike = int(kraw) / 1000.0
        oi = float(o.get("open_interest") or 0)
        gamma = float(o.get("gamma") or 0)
        gex_1pct = oi * gamma * 100.0 * (spot ** 2) * 0.01
        if cp == "C":
            by_strike[strike]["oi_c"] += oi
            by_strike[strike]["gex"] += gex_1pct
        else:
            by_strike[strike]["oi_p"] += oi
            by_strike[strike]["gex"] -= gex_1pct

    if not by_strike:
        return {"error": f"Sin contratos dentro de {horizon} días", "id": symbol}

    strikes = sorted(by_strike.keys())
    call_wall = max(strikes, key=lambda k: by_strike[k]["oi_c"])
    put_wall = max(strikes, key=lambda k: by_strike[k]["oi_p"])
    max_pain = calc_max_pain(by_strike, spot)
    strike_gex = [(k, by_strike[k]["gex"]) for k in strikes]
    flip = calc_gamma_flip(strike_gex)
    total_gex = sum(g for _, g in strike_gex)

    oi_c = sum(by_strike[k]["oi_c"] for k in strikes)
    oi_p = sum(by_strike[k]["oi_p"] for k in strikes)
    pcr_oi = (oi_p / oi_c) if oi_c > 0 else None

    puts_below = sorted(
        [k for k in strikes if k <= spot],
        key=lambda k: by_strike[k]["oi_p"],
        reverse=True,
    )[:5]
    calls_above = sorted(
        [k for k in strikes if k >= spot],
        key=lambda k: by_strike[k]["oi_c"],
        reverse=True,
    )[:5]

    filas = []
    for k in strikes:
        v = by_strike[k]
        filas.append({"k": k, "oi_c": v["oi_c"], "oi_p": v["oi_p"], "gex": v["gex"]})

    mov = None
    if call_wall and put_wall:
        mov = abs(call_wall - put_wall) / 4.0

    return {
        "id": symbol,
        "nombre": symbol,
        "px": spot,
        "ts": datetime.now().strftime("%H:%M:%S"),
        "fuente": f"CBOE delayed · {cboe_sym}",
        "filas": filas,
        "res": {
            "pcr_oi": pcr_oi,
            "pcr_v": None,
            "gex": total_gex,
            "flip": flip,
            "max_dolor": max_pain,
            "venc0": nearest_exp.isoformat() if nearest_exp else None,
            "mov": mov,
            "mov_pct": (mov / spot * 100) if mov and spot else None,
            "zonas_p": puts_below,
            "zonas_c": calls_above,
            "call_wall": call_wall,
            "put_wall": put_wall,
        },
    }


def fetch_yahoo_bars(symbol, range_="3mo", interval="1d"):
    ysym = YAHOO_CHART.get(symbol, symbol)
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + quote(ysym)
        + f"?interval={interval}&range={range_}"
    )
    raw = http_json(url)
    result = (raw.get("chart") or {}).get("result") or [None]
    result = result[0]
    if not result:
        raise ValueError("sin datos de precio")
    ts = result.get("timestamp") or []
    quote_ = (result.get("indicators") or {}).get("quote") or [{}]
    closes = (quote_[0] or {}).get("close") or []
    bars = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        bars.append({"time": int(t), "value": float(c)})
    return {"s": symbol, "yahoo": ysym, "bars": bars}


def cached_build(symbol, horizon):
    key = f"{symbol}:{horizon}"
    now = time.time()
    if key in _cache and now - _cache[key]["t"] < CACHE_TTL:
        return _cache[key]["data"]
    data = build_from_cboe(symbol, horizon)
    _cache[key] = {"t": now, "data": data}
    return data


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

    def _json(self, status, obj):
        body = json.dumps(obj, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/api/calor/datos", "/api/calor/vivo"):
            sym = (qs.get("s") or ["QQQ"])[0].upper()
            horizon = int((qs.get("h") or ["30"])[0])
            try:
                data = cached_build(sym, horizon)
                if path.endswith("vivo"):
                    self._json(200, {
                        "px": data.get("px"),
                        "fuente": data.get("fuente", "CBOE"),
                        "id": sym,
                    })
                else:
                    self._json(200, data)
            except Exception as e:
                self._json(502, {"error": str(e), "id": sym})
            return

        if path == "/api/precios":
            sym = (qs.get("s") or ["QQQ"])[0].upper()
            try:
                self._json(200, fetch_yahoo_bars(
                    sym,
                    range_=(qs.get("r") or ["3mo"])[0],
                    interval=(qs.get("i") or ["1d"])[0],
                ))
            except Exception as e:
                self._json(502, {"error": str(e)})
            return

        if path == "/activos":
            self._json(200, ACTIVOS)
            return

        if path in ("/", "/index.html", "/mapa"):
            self.path = "/mapa_calor_live.html"
            return super().do_GET()

        return super().do_GET()

    def log_message(self, fmt, *args):
        msg = fmt % args
        if "/api/" in msg:
            print(f"  {msg}")


def main():
    html_path = os.path.join(DIR, "mapa_calor_live.html")
    if not os.path.exists(html_path):
        print("ERROR: falta mapa_calor_live.html en esta carpeta")
        return

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print("=" * 58)
    print("  MAPA DE CALOR · Plan B (CBOE + cálculo Python)")
    print("=" * 58)
    print(f"  Abre: {url}")
    print("  Fuente: CBOE delayed (OI + gamma) · sin API key")
    print("  Calcula: Max Pain, Walls, GEX, Gamma Flip")
    print(f"  Activos: {', '.join(ACTIVOS)}")
    print("  Ctrl+C para detener")
    print("=" * 58)

    def open_browser():
        time.sleep(0.7)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
