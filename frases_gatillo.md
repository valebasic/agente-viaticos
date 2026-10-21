# Frases para probar el gatillo de tu skill

La descripción de una skill es lo único que Claude lee antes de decidir si la usa. Estas cuatro frases sirven para probar si tu descripción funciona.

Prueba **cada frase en una sesión nueva** de Claude Code. Cuando una skill se carga, sus instrucciones se quedan en la conversación, y la siguiente prueba ya no sería válida.

| # | Frase | ¿Debe activar `revisar-gastos`? | ¿Se activó? |
|---|---|---|---|
| 1 | Me llegó la legalización de Andrés Quintero. ¿Está todo en regla? El archivo es datos/legalizacion_L-2031.csv | Sí | |
| 2 | ¿Cuánto hay que reembolsarle a Andrés por el viaje a Bucaramanga? Sus gastos están en la carpeta datos/. | Sí | |
| 3 | ¿Cuál es el tope de hospedaje por noche en Cartagena? | No | |
| 4 | Crea un archivo CSV de ejemplo con cinco gastos de viaje inventados para una prueba. | No | |

## Cómo saber si se activó

En la conversación aparece el uso de la herramienta **Skill** con el nombre de tu skill. Si no lo ves, cambia a la vista detallada con `Ctrl+O`.

## Reto

1. Anota tu puntaje: cuántas de las cuatro frases se comportaron como debían.
2. Si no llegaste a 4 de 4, reescribe la descripción y repite.
3. Publica tu descripción. Gana quien logre 4 de 4 con la descripción más corta.
4. Intenta romper la descripción de un compañero: escribe una frase que debería activarla y no lo hace, o una que la activa sin deber.

## Pistas para una buena descripción

- Di **qué hace** la skill y **cuándo usarla**.
- Usa las palabras que diría quien la necesita: legalización, reembolso, revisar, validar.
- Pon primero el caso de uso principal: las descripciones largas se recortan.
- Si hay algo para lo que no debe usarse, dilo.
