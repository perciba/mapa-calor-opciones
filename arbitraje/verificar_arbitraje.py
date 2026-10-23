#!/usr/bin/env python3
"""
Verificador de arbitraje / margen de casa — educativo.
NO promete ganancias. Solo comprueba la matemática con cuotas reales que tú ingresas.

Uso rápido:
  python3 verificar_arbitraje.py
  python3 verificar_arbitraje.py --demo
  python3 verificar_arbitraje.py --web
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class Resultado:
    nombre: str
    cuota: float
    casa: str = ""


def margen_casa(cuotas: List[float]) -> float:
    """Margen implícito de la casa (%). >0 = ventaja de la casa."""
    s = sum(1.0 / c for c in cuotas)
    return (s - 1.0) * 100.0


def hay_arbitraje(cuotas: List[float]) -> bool:
    """True si sum(1/cuota) < 1 (cobertura teórica con beneficio)."""
    return sum(1.0 / c for c in cuotas) < 1.0 - 1e-12


def stakes_arbitraje(cuotas: List[float], bank: float = 100.0) -> List[float]:
    inv = [1.0 / c for c in cuotas]
    total_inv = sum(inv)
    return [bank * (i / total_inv) for i in inv]


def retorno_garantizado(cuotas: List[float], stakes: List[float]) -> float:
    returns = [stakes[i] * cuotas[i] for i in range(len(cuotas))]
    return min(returns)


def analizar(resultados: List[Resultado], bank: float = 100.0) -> dict:
    cuotas = [r.cuota for r in resultados]
    if any(c <= 1.0 for c in cuotas):
        raise ValueError("Todas las cuotas deben ser > 1.0")

    inv_sum = sum(1.0 / c for c in cuotas)
    m = margen_casa(cuotas)
    arb = hay_arbitraje(cuotas)
    stakes = stakes_arbitraje(cuotas, bank)
    ret = retorno_garantizado(cuotas, stakes)
    profit = ret - bank

    detalle = []
    for i, r in enumerate(resultados):
        detalle.append({
            "resultado": r.nombre,
            "casa": r.casa or "—",
            "cuota": round(r.cuota, 3),
            "stake": round(stakes[i], 2),
            "retorno_si_gana": round(stakes[i] * r.cuota, 2),
            "prob_implicita_%": round(100.0 / r.cuota, 2),
        })

    return {
        "arbitraje_teorico": arb,
        "suma_1_sobre_cuota": round(inv_sum, 6),
        "margen_casa_%": round(m, 3),
        "bank": bank,
        "retorno_minimo": round(ret, 2),
        "beneficio_teorico": round(profit, 2),
        "beneficio_teorico_%": round(profit / bank * 100, 3),
        "detalle": detalle,
        "aviso": (
            "ARBITRAJE TEÓRICO: la suma 1/cuota < 1. "
            "En la práctica: límites de cuenta, cambios de cuota, reglas distintas y errores de liquidación."
            if arb else
            "NO hay arbitraje: la casa (o el conjunto de cuotas) tiene margen a su favor."
        ),
    }


def imprimir(reporte: dict) -> None:
    print()
    print("=" * 56)
    print("  VERIFICADOR DE ARBITRAJE / MARGEN")
    print("=" * 56)
    print(f"  Suma 1/cuota     : {reporte['suma_1_sobre_cuota']}")
    print(f"  Margen casa (%)  : {reporte['margen_casa_%']}%")
    print(f"  ¿Arbitraje?      : {'SÍ (teórico)' if reporte['arbitraje_teorico'] else 'NO'}")
    print(f"  Bank             : {reporte['bank']}")
    print(f"  Retorno mínimo   : {reporte['retorno_minimo']}")
    print(f"  Beneficio teórico: {reporte['beneficio_teorico']} ({reporte['beneficio_teorico_%']}%)")
    print("-" * 56)
    for d in reporte["detalle"]:
        casa = f" [{d['casa']}]" if d['casa'] != "—" else ""
        print(
            f"  {d['resultado']}{casa}: cuota {d['cuota']} | "
            f"stake {d['stake']} | si gana → {d['retorno_si_gana']} | "
            f"prob ~{d['prob_implicita_%']}%"
        )
    print("-" * 56)
    print(f"  {reporte['aviso']}")
    print("=" * 56)
    print()


def demo() -> dict:
    print("\n>>> DEMO A — Mercado típico 1X2 (sin arbitraje)")
    a = analizar([
        Resultado("Local", 2.10, "Casa A"),
        Resultado("Empate", 3.20, "Casa A"),
        Resultado("Visitante", 3.40, "Casa A"),
    ], bank=100)
    imprimir(a)

    print(">>> DEMO B — Cuotas cruzadas que generan arbitraje TEÓRICO")
    print("    (números inventados solo para verificar la fórmula)\n")
    b = analizar([
        Resultado("Local", 2.20, "BetA"),
        Resultado("Empate", 3.80, "BetB"),
        Resultado("Visitante", 4.50, "BetC"),
    ], bank=100)
    imprimir(b)

    assert a["arbitraje_teorico"] is False
    assert b["arbitraje_teorico"] is True
    assert b["beneficio_teorico"] > 0
    rets = [d["retorno_si_gana"] for d in b["detalle"]]
    assert max(rets) - min(rets) < 0.05, rets
    print("✓ Autotest OK: la matemática del arbitraje se verifica correctamente.\n")
    return b


def interactivo() -> None:
    print("\nIngresa resultados y cuotas (ej. fútbol 1X2 o Moneyline).")
    print("Deja el nombre vacío para terminar.\n")
    items: List[Resultado] = []
    while True:
        nombre = input("  Nombre del resultado (Local/Empate/Visitante/...): ").strip()
        if not nombre:
            break
        casa = input("  Casa (opcional): ").strip()
        while True:
            try:
                cuota = float(input("  Cuota (ej. 2.15): ").strip().replace(",", "."))
                if cuota <= 1.0:
                    print("    La cuota debe ser > 1")
                    continue
                break
            except ValueError:
                print("    Número inválido")
        items.append(Resultado(nombre, cuota, casa))
        print()

    if len(items) < 2:
        print("Se necesitan al menos 2 resultados.")
        return

    bank_s = input("Bank total a repartir [100]: ").strip() or "100"
    bank = float(bank_s.replace(",", "."))
    reporte = analizar(items, bank=bank)
    imprimir(reporte)

    if reporte["arbitraje_teorico"]:
        print("VERIFICACIÓN MANUAL:")
        print(f"  Suma de stakes = {sum(d['stake'] for d in reporte['detalle']):.2f}")
        for d in reporte["detalle"]:
            print(f"  Si gana {d['resultado']}: recibes {d['retorno_si_gana']:.2f}")
        print(
            f"  Diferencia máx entre retornos: "
            f"{max(d['retorno_si_gana'] for d in reporte['detalle']) - min(d['retorno_si_gana'] for d in reporte['detalle']):.4f}"
        )
        print()


def servir_web(port: int = 8770) -> None:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse
    import webbrowser
    import threading
    import time

    HTML = r"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Verificador de arbitraje</title>
<style>
body{font-family:system-ui,sans-serif;background:#0b0f14;color:#e8eef6;margin:0;padding:20px}
h1{font-size:1.2rem} .card{background:#141b24;border:1px solid #243041;border-radius:12px;padding:16px;max-width:720px;margin:0 auto}
label{display:block;font-size:.8rem;color:#8b9cb3;margin-top:10px}
input,button{width:100%;padding:8px;margin-top:4px;border-radius:8px;border:1px solid #243041;background:#0b0f14;color:#e8eef6;box-sizing:border-box}
button{background:#06b6d4;color:#0b0f14;font-weight:700;border:none;cursor:pointer;margin-top:14px}
.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.ok{color:#22c55e}.bad{color:#ef4444}.muted{color:#8b9cb3;font-size:.85rem}
table{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:10px}
td,th{padding:6px;border-bottom:1px solid #243041;text-align:left}
.warn{background:#422006;border:1px solid #f59e0b;color:#fde68a;padding:10px;border-radius:8px;font-size:.82rem;margin-top:12px}
@media(max-width:700px){.row{grid-template-columns:1fr}}
</style></head><body>
<div class="card">
<h1>Verificador de arbitraje / margen</h1>
<p class="muted">Pega cuotas reales de tus casas. Solo comprueba la matemática — no es una apuesta segura.</p>
<div class="row">
  <div><label>Resultado 1</label><input id="n1" value="Local"/><label>Cuota</label><input id="c1" value="2.10"/><label>Casa</label><input id="h1" value="Casa A"/></div>
  <div><label>Resultado 2</label><input id="n2" value="Empate"/><label>Cuota</label><input id="c2" value="3.40"/><label>Casa</label><input id="h2" value="Casa B"/></div>
  <div><label>Resultado 3 (opcional)</label><input id="n3" value="Visitante"/><label>Cuota</label><input id="c3" value="3.60"/><label>Casa</label><input id="h3" value="Casa C"/></div>
</div>
<label>Bank</label><input id="bank" value="100"/>
<button onclick="calcular()">Calcular / verificar</button>
<div id="out"></div>
<div class="warn"><strong>Aviso:</strong> Un arbitraje teórico no garantiza dinero. Las casas limitan cuentas, cambian cuotas y tienen reglas distintas. Uso educativo.</div>
</div>
<script>
async function calcular(){
  const items=[];
  for(const i of [1,2,3]){
    const n=document.getElementById('n'+i).value.trim();
    const c=parseFloat(String(document.getElementById('c'+i).value).replace(',','.'));
    const h=document.getElementById('h'+i).value.trim();
    if(n && c>1) items.push({nombre:n,cuota:c,casa:h});
  }
  const bank=parseFloat(String(document.getElementById('bank').value).replace(',','.'))||100;
  const r=await fetch('/api/analizar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items,bank})});
  const j=await r.json();
  if(j.error){document.getElementById('out').innerHTML='<p class="bad">'+j.error+'</p>';return;}
  let html='<p class="'+(j.arbitraje_teorico?'ok':'bad')+'"><strong>'+(j.arbitraje_teorico?'Arbitraje TEÓRICO detectado':'Sin arbitraje')+
    '</strong> · margen '+j['margen_casa_%']+'% · suma 1/cuota = '+j.suma_1_sobre_cuota+'</p>';
  html+='<p class="muted">Beneficio teórico: '+j.beneficio_teorico+' ('+j['beneficio_teorico_%']+'%) sobre bank '+j.bank+'</p>';
  html+='<table><tr><th>Resultado</th><th>Casa</th><th>Cuota</th><th>Stake</th><th>Si gana</th></tr>';
  for(const d of j.detalle){
    html+='<tr><td>'+d.resultado+'</td><td>'+d.casa+'</td><td>'+d.cuota+'</td><td>'+d.stake+'</td><td>'+d.retorno_si_gana+'</td></tr>';
  }
  html+='</table><p class="muted">'+j.aviso+'</p>';
  document.getElementById('out').innerHTML=html;
}
</script>
</body></html>
"""

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if urlparse(self.path).path in ("/", "/index.html"):
                body = HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if urlparse(self.path).path != "/api/analizar":
                self.send_response(404)
                self.end_headers()
                return
            n = int(self.headers.get("Content-Length", 0))
            raw = json.loads(self.rfile.read(n).decode() or "{}")
            try:
                items = [
                    Resultado(i["nombre"], float(i["cuota"]), i.get("casa") or "")
                    for i in raw.get("items") or []
                ]
                if len(items) < 2:
                    raise ValueError("Mínimo 2 resultados con cuota > 1")
                rep = analizar(items, bank=float(raw.get("bank") or 100))
                body = json.dumps(rep).encode()
                self.send_response(200)
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode()
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", port), H)
    url = f"http://127.0.0.1:{port}"
    print(f"Web verificador: {url}")
    print("Ctrl+C para detener")

    def open_b():
        time.sleep(0.6)
        webbrowser.open(url)

    threading.Thread(target=open_b, daemon=True).start()
    server.serve_forever()


def main():
    p = argparse.ArgumentParser(description="Verificador de arbitraje (educativo)")
    p.add_argument("--demo", action="store_true", help="Correr demos + autotest")
    p.add_argument("--web", action="store_true", help="Abrir UI local")
    p.add_argument("--port", type=int, default=8770)
    p.add_argument("--json", action="store_true", help="Con --demo, imprimir JSON del caso B")
    args = p.parse_args()

    if args.demo:
        rep = demo()
        if args.json:
            print(json.dumps(rep, indent=2, ensure_ascii=False))
        return
    if args.web:
        servir_web(args.port)
        return
    interactivo()


if __name__ == "__main__":
    main()
