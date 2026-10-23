# Mapa de Calor · Opciones

Dashboard de Open Interest, Max Pain y Gamma (GEX) con datos reales.

## Activos
NDX (NAS100), QQQ, SPX, SPY, IWM, AAPL, NVDA, TSLA, COIN, **BTC**, **ETH**, VIX

## Cómo usarlo

1. Descarga el ZIP o clona el repo.
2. Abre una terminal **en la carpeta del proyecto**.
3. Ejecuta:

```bash
python3 servidor_mapa.py
```

4. Se abre el navegador en http://127.0.0.1:8765

**Importante:** no abras el HTML con doble clic. Siempre usa el servidor.

## Mejoras incluidas

- Lectura rápida (GEX larga/corta + PCR)
- Distancia % al Max Pain, Call Wall y Put Wall
- Niveles listos para **TradingView** (copiar Pine Script)
- BTC y ETH
- Auto-refresh cada 60s

## TradingView

1. Elige un activo en el dashboard.
2. Pulsa **Copiar Pine Script**.
3. En TradingView → Pine Editor → pega → Añadir a gráfico.
4. Verás Max Pain, Call Wall, Put Wall y zonas de OI.

## Archivos

| Archivo | Uso |
|---------|-----|
| `servidor_mapa.py` | Servidor local + proxy API |
| `mapa_calor_live.html` | Dashboard (datos reales) |

## Nota
Depende de que la API de origen (túnel Cloudflare) siga activa. Uso educativo.
