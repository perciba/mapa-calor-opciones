# Mapa de Calor · Opciones (Plan B)

Dashboard local **sin API propia ni API key**.

## Fuente de datos

| Dato | Fuente |
|------|--------|
| OI, gamma, cadena | **CBOE delayed** (~15 min) |
| Max Pain, Walls, GEX, Flip | **Calculado en Python** |
| Precio histórico | Yahoo Finance |

## Cómo usar

1. Descarga el ZIP del repo.
2. En la carpeta:

```bash
python3 servidor_mapa.py
```

3. Abre http://127.0.0.1:8765

**No abras el HTML a doble clic** — siempre el servidor.

## Activos

NDX (vía QQQ), QQQ, SPX, SPY, IWM, AAPL, NVDA, TSLA, COIN, VIX.  
BTC/ETH: solo precio (no hay cadena equity CBOE).

## Qué calcula Python

- **Max Pain** — strike que minimiza el valor de opciones al vencimiento
- **Call Wall / Put Wall** — strikes con más open interest
- **GEX** — exposición gamma aproximada (OI × gamma CBOE × convención dealers)
- **Gamma Flip** — donde el GEX acumulado cruza cero

## Archivos

| Archivo | Uso |
|---------|-----|
| `servidor_mapa.py` | Backend Plan B |
| `mapa_calor_live.html` | Dashboard |

Uso educativo. No es consejo financiero.
