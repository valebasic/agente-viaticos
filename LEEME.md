# Kit de la sesión 6

Material del curso *Desarrollo de Aplicaciones con IA*. Todos los datos son **ficticios**: la empresa Altiplano S.A.S., sus empleados y sus gastos no existen.

## Qué contiene

| Archivo | Qué es |
|---|---|
| `datos/legalizacion_L-2031.csv` | La legalización de un viaje: 14 gastos de un empleado |
| `formato_informe.md` | El formato y los veredictos que debe usar tu skill al revisar una legalización |
| `conocimiento/politica_viaticos.md` | La política de viáticos 2.0, la misma de la sesión 4 |
| `frases_gatillo.md` | Cuatro frases para probar la descripción de tu skill |

## Cómo usarlo

1. Descomprime el kit.
2. Copia la carpeta `datos/` y los archivos `formato_informe.md` y `frases_gatillo.md` a la raíz del proyecto de tu agente, el mismo de las sesiones anteriores.
3. Si en tu proyecto ya existe `conocimiento/politica_viaticos.md`, no la reemplaces. Si no existe, copia también la carpeta `conocimiento/`.
4. No cambies el contenido de los archivos. Todos los compañeros deben tener los mismos datos para llegar al mismo total.

## Qué es una legalización

Cuando un empleado regresa de un viaje de trabajo, presenta sus gastos para que la empresa se los reembolse. Ese paquete de gastos es la legalización. Contabilidad revisa cada gasto contra la política y decide cuánto se reembolsa.

Cada archivo de legalización corresponde a **un viaje de un empleado**.

## Columnas del archivo

| Columna | Significado |
|---|---|
| `legalizacion` | Número de la legalización |
| `empleado` | Persona que viajó |
| `ciudad` | Ciudad de destino |
| `salida` | Fecha de salida del viaje, en formato AAAA-MM-DD |
| `regreso` | Fecha de regreso del viaje |
| `id` | Identificador del gasto |
| `fecha` | Fecha del gasto |
| `categoria` | Alimentación, Hospedaje, Transporte terrestre, Tiquetes aéreos u Otros |
| `descripcion` | Detalle del gasto |
| `factura` | Número de la factura electrónica. Vacío si el gasto no tiene factura |
| `valor_cop` | Valor en pesos colombianos, sin puntos ni comas |

Las cinco primeras columnas describen el viaje y se repiten en todas las filas. En Alimentación y Transporte terrestre, cada fila es el total de ese día. En Hospedaje, cada fila es una noche.

## La trampa del "gratis"

En el ejercicio 3 tu agente envía a la API de Gemini las instrucciones de tu skill y el informe de la legalización. En el nivel gratuito eso tiene dos limitaciones críticas:

- **Privacidad.** Google se reserva el derecho de usar lo que envías (instrucciones, documentos, código) para entrenar y mejorar sus modelos, incluso con revisión humana. Una skill contiene la forma de trabajar de tu equipo: si la envías con datos reales, estás regalando las dos cosas. Para proteger los datos hay que habilitar la facturación y pasar al nivel de pago, donde no se usan para entrenamiento.
- **Límites de uso.** Hay topes estrictos de solicitudes por minuto, tokens por minuto y solicitudes por día. Un agente con herramientas trabaja en ciclos: cada pregunta que usa una skill son tres llamadas (cargar la skill, ejecutar el script y responder). Si preguntas muy rápido verás el error 429. Espera un minuto y vuelve a intentar.

Por eso en este curso solo trabajamos con datos ficticios o anonimizados.
