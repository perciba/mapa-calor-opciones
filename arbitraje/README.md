# Verificador de arbitraje / margen (educativo)

Herramienta **real** para comprobar la matemática de:

- margen de la casa
- arbitraje teórico entre cuotas
- stakes proporcionales

**No es un sistema de apuestas seguras.** Sirve para verificar números que tú copias de casas (incluidas colombianas).

## Cómo verificar que funciona

```bash
cd arbitraje
python3 verificar_arbitraje.py --demo
```

Debes ver:

1. **Demo A** — mercado normal → `¿Arbitraje? NO` y margen positivo de la casa.
2. **Demo B** — cuotas cruzadas artificiales → `¿Arbitraje? SÍ (teórico)` y beneficio > 0.
3. Línea final: `✓ Autotest OK`.

## Usar con cuotas reales

**Terminal (interactivo):**

```bash
python3 verificar_arbitraje.py
```

**Web local:**

```bash
python3 verificar_arbitraje.py --web
```

Abre http://127.0.0.1:8770 y pega cuotas de tus casas.

## Fórmula que se verifica

- Suma `1/cuota` de todos los resultados del mercado.
- Si la suma **< 1** → arbitraje teórico.
- Si la suma **> 1** → margen a favor de la casa.
- Stakes: proporcionales a `1/cuota` para igualar el retorno en cada resultado.

## Aviso

Límites de cuenta, cuotas que cambian, reglas distintas y errores de liquidación hacen que un arbitraje en pantalla no sea dinero garantizado.
