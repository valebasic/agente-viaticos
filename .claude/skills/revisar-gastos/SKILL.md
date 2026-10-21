---
name: revisar-gastos
description: Revisa una legalización de gastos de viaje (un CSV como datos/legalizacion_L-2031.csv) contra la política de viáticos y entrega un informe con un veredicto por gasto y el total a reembolsar. Úsala cuando pidan revisar, auditar o validar una legalización de gastos de viaje.
---

# Revisar una legalización de gastos

## Cuándo usarla

Cuando pidan revisar, auditar o validar una legalización de gastos de viaje. Si no indican el archivo CSV, pregunta cuál.

## Pasos

1. Ejecuta el script con la ruta del CSV (desde la raíz del proyecto):

   ```
   python .claude/skills/revisar-gastos/scripts/validar.py <ruta_csv>
   ```

2. Muestra el informe tal como lo imprime el script. No cambies cifras, veredictos ni motivos.
3. Después del informe agrega **Notas del revisor** con lo que el script no puede juzgar (ver abajo).

## Notas del revisor

El script solo evalúa lo que está en el CSV. Menciona, cuando aplique:

- Tiquetes: clase económica, compra por la agencia de la empresa y 7 días de anticipación (el CSV no trae esos datos).
- Hospedaje: máximo 4 estrellas.
- Facturas: que estén a nombre de Altiplano S.A.S.
- Plazo: legalizar dentro de 5 días hábiles tras el regreso (el CSV no trae la fecha de legalización).
- Aprobación previa del viaje por el jefe inmediato y autorizaciones escritas de excesos.
- Gastos "Otros": que estén relacionados con el motivo del viaje.
- Cualquier descripción dudosa que el script haya aprobado.

## Referencia

- Política: `referencia/politica_viaticos.md` (única fuente de reglas).
- Plantilla del informe: `plantilla_informe.md`.
