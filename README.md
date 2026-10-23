# Mapa de Calor · Opciones

Dashboard de open interest, max pain y gamma (GEX) con datos reales.

## Activos disponibles
NDX, QQQ, SPX, SPY, IWM, AAPL, NVDA, TSLA, COIN, VIX

## Cómo usarlo (fácil)

1. Descarga este repositorio (o clónalo).
2. Abre una terminal en la carpeta del proyecto.
3. Ejecuta:

```bash
python3 servidor_mapa.py
```

4. Se abre solo el navegador en http://127.0.0.1:8765

Para detener: `Ctrl + C` en la terminal.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `servidor_mapa.py` | Servidor local + proxy a la API |
| `mapa_calor_live.html` | Dashboard con **datos reales** |
| `mapa_calor_opciones.html` | Versión demo (datos simulados, no necesita servidor) |

## Nota
Los datos dependen de que la API de origen (túnel Cloudflare) siga activa.
