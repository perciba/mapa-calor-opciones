# Mapa de Calor · Opciones

Dashboard local: Open Interest, Max Pain, GEX, **Gamma Flip** y gráfico de precio con niveles.

## Cómo usar

1. Descarga el ZIP del repo.
2. En la carpeta:

```bash
python3 servidor_mapa.py
```

3. Abre http://127.0.0.1:8765

**No abras el HTML con doble clic** — siempre el servidor.

## Incluye

- Activos: NDX, QQQ, SPX, SPY, IWM, AAPL, NVDA, TSLA, COIN, BTC, ETH, VIX
- Gamma Flip (cero GEX)
- Lectura rápida GEX / PCR
- Distancia % a niveles
- **Gráfico de precio** (3 meses) con líneas: Spot, Flip, Max Pain, Call Wall, Put Wall
- Pine Script para TradingView
- Datos de opciones vía API original + precios vía Yahoo (gratis)

## Archivos

| Archivo | Uso |
|---------|-----|
| `servidor_mapa.py` | Servidor + proxy API + `/api/precios` |
| `mapa_calor_live.html` | Dashboard |

Uso educativo. No es consejo financiero.
