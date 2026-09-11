# Reporte de mapeo de series BCRA

Generado automáticamente por `scripts/bcra/download.py` el 2026-09-11T14:47:52.412490+00:00 (UTC).

Este archivo se regenera en cada corrida. No editar a mano: para
corregir un mapeo, ajustar `scripts/bcra/config.py` y volver a correr
el script.

| clave estandarizada | estado | idVariable | descripción original |
|---|---|---|---|
| `base_monetaria` | ok | 15 | Base monetaria |
| `circulante` | ok | 16 | Circulación monetaria |
| `billetes_monedas_publico` | ok | 17 | Billetes y monedas en poder del público |
| `depositos_pesos` | ok | 91 | Depósitos en pesos de los sectores público y privados no financieros (incluye cedros) |
| `depositos_sector_privado` | ok | 1526 | Depósitos totales del sector privado |
| `m1` | ok | 1612 | M1 en moneda local |
| `m2` | ok | 109 | M2 |
| `m3` | ok | 1624 | M3 en moneda local |
| `reservas_internacionales` | ok | 1 | Reservas internacionales |
| `efectivo_entidades_financieras` | ok | 18 | Efectivo en entidades financieras. |
| `tasa_politica_monetaria` | **sin match** | — | — |
| `badlar_privados` | **ambiguo (2 candidatos)** | — | 7: Tasa de interés BADLAR de bancos privados; 35: Tasa de interés BADLAR de bancos privados |
| `tamar` | **ambiguo (2 candidatos)** | — | 44: Tasa de interes TAMAR de bancos privados; 45: Tasa de interés TAMAR de bancos privados |
| `call_interbancario` | **sin match** | — | — |

## Pendientes de revisión manual

- `tasa_politica_monetaria` (tasas_monetarias): sin_match. Verificado 2026-09-11: sin serie vigente. Los únicos candidatos parecidos en el catálogo (idVariable 160 y 161, 'Tasas de interés de política monetaria') dejaron de actualizarse en julio 2025 — el BCRA aparenta haber discontinuado esta serie al cambiar de esquema de política monetaria. Pendiente: decidir si se deja sin dato, o se reemplaza el concepto por la tasa que el BCRA use actualmente como referencia de política (a confirmar).
- `badlar_privados` (tasas_monetarias): ambiguo. PENDIENTE DE CONFIRMAR A MANO (no resuelto automáticamente a propósito). El catálogo tiene 2 series activas en 'Principales Variables' con la MISMA descripción ('Tasa de interés BADLAR de bancos privados') pero valores distintos el 2026-09-09: idVariable 7 = 22.4375%, idVariable 35 = 24.88%. No hay forma de distinguir cuál es 'la' oficial solo con los metadatos del catálogo. Una vez confirmado cuál corresponde, agregar acá `exact=("Tasa de interés BADLAR de bancos privados",)` no alcanza para desambiguar (las dos tienen el mismo texto): hay que fijar el idVariable a mano editando `bcra_client.py` o agregando un filtro adicional por idVariable en el matcher.
- `tamar` (tasas_monetarias): ambiguo. PENDIENTE DE CONFIRMAR A MANO (mismo caso que badlar_privados). Bug corregido 2026-09-11: el include anterior (solo 'tamar') matcheaba también series de la provincia de 'CaTAMARca'; se agregó 'bancos' como segundo término requerido. El catálogo tiene 2 series activas en 'Principales Variables' con valores distintos el 2026-09-09: idVariable 44 ('Tasa de interes TAMAR...', sin tilde) = 23.5625%, idVariable 45 ('Tasa de interés TAMAR...', con tilde) = 26.27%.
- `call_interbancario` (tasas_monetarias): sin_match. Verificado 2026-09-11: sin ningún candidato en el catálogo actual (cero series con 'call' en la descripción). El BCRA no parece publicar hoy una serie con este nombre; pendiente investigar bajo qué otro nombre podría estar publicada la tasa call interbancaria, si es que sigue existiendo.
