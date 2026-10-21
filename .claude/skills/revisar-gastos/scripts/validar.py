"""Valida una legalización de gastos de viaje contra la política de viáticos v2.0.

Uso: python validar.py <ruta_csv>
Imprime el informe llenando plantilla_informe.md.
"""
import csv
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from string import Template

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantilla_informe.md"

GRUPO_A = {"bogota", "medellin", "cartagena"}
TOPE_ALIMENTACION_DIA = 95_000
TOPE_HOSPEDAJE_NOCHE = {"A": 320_000, "B": 240_000}
TOPE_TRANSPORTE_DIA = 60_000
UMBRAL_FACTURA = 30_000
UMBRAL_DIRECTOR = 1_500_000
NO_REEMBOLSABLES = [
    "minibar", "alcohol", "licor", "cerveza", "vino", "propina",
    "multa", "comparendo", "cine", "concierto", "tour", "acompanante",
]


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower().strip()


def pesos(valor):
    return f"${valor:,.0f}".replace(",", ".") + " COP"


def leer_valor(texto):
    try:
        valor = int(str(texto).strip())
    except ValueError:
        return None
    return valor if valor > 0 else None


def revisar_fechas_y_duplicados(filas):
    """Por fila: (veredicto, motivo) si la fecha está fuera del viaje o la factura
    ya se presentó antes; None si no hay problema."""
    vistas = set()
    previos = []
    for f in filas:
        factura = f["factura"].strip().upper()
        cat = normalizar(f["categoria"])
        if factura and factura in vistas:
            previos.append(("Rechazado", f"Sección 5: la factura {factura} ya fue presentada en otro gasto (duplicado)."))
            continue
        if factura:
            vistas.add(factura)
        if cat != "tiquetes aereos" and not f["salida"] <= f["fecha"] <= f["regreso"]:
            previos.append(("Devuelto", f"Sección 2: la fecha está fuera del viaje ({f['salida']} a {f['regreso']}); no se puede confirmar que sea del viaje."))
            continue
        previos.append(None)
    return previos


def evaluar(filas, grupo):
    """Devuelve una lista de (veredicto, motivo) en el orden de las filas."""
    previos = revisar_fechas_y_duplicados(filas)
    totales = defaultdict(int)
    for f, previo in zip(filas, previos):
        if f["_valor"] is not None and previo is None:
            totales[(normalizar(f["categoria"]), f["fecha"])] += f["_valor"]

    resultados = []
    for f, previo in zip(filas, previos):
        if previo:
            resultados.append(previo)
            continue
        cat = normalizar(f["categoria"])
        texto = normalizar(f["categoria"] + " " + f["descripcion"])
        valor = f["_valor"]

        if valor is None:
            resultados.append(("Devuelto", "Sección 5: el valor falta o no es válido."))
            continue
        if any(p in texto for p in NO_REEMBOLSABLES):
            resultados.append(("Rechazado", "Sección 6: gasto no reembolsable."))
            continue

        suma = totales[(cat, f["fecha"])]
        if cat == "alimentacion" and suma > TOPE_ALIMENTACION_DIA:
            resultados.append(("Rechazado", f"Secciones 2 y 4: alimentación del día suma {pesos(suma)}, supera el tope de {pesos(TOPE_ALIMENTACION_DIA)} por día."))
            continue
        if cat == "hospedaje" and suma > TOPE_HOSPEDAJE_NOCHE[grupo]:
            resultados.append(("Rechazado", f"Secciones 2 y 4: supera el tope de {pesos(TOPE_HOSPEDAJE_NOCHE[grupo])} por noche del Grupo {grupo}."))
            continue
        if cat == "transporte terrestre" and suma > TOPE_TRANSPORTE_DIA:
            resultados.append(("Rechazado", f"Secciones 2 y 4: transporte del día suma {pesos(suma)}, supera el tope de {pesos(TOPE_TRANSPORTE_DIA)} por día."))
            continue

        if valor > UMBRAL_FACTURA and not f["factura"].strip():
            resultados.append(("Devuelto", "Sección 5: gasto mayor a $30.000 COP sin factura electrónica."))
            continue
        if valor > UMBRAL_DIRECTOR:
            resultados.append(("Devuelto", "Sección 3: supera $1.500.000 COP y no hay aprobación del director en el archivo (queda Pendiente)."))
            continue
        resultados.append(("Aprobado", ""))
    return resultados


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python validar.py <ruta_csv>")
    with open(sys.argv[1], encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        sys.exit("El archivo no tiene gastos.")

    for f in filas:
        f["_valor"] = leer_valor(f["valor_cop"])
    primera = filas[0]
    grupo = "A" if normalizar(primera["ciudad"]) in GRUPO_A else "B"
    resultados = evaluar(filas, grupo)

    lineas = []
    cuenta = {"Aprobado": 0, "Rechazado": 0, "Devuelto": 0}
    total = 0
    for f, (veredicto, motivo) in zip(filas, resultados):
        cuenta[veredicto] += 1
        if veredicto == "Aprobado":
            total += f["_valor"]
        valor = pesos(f["_valor"]) if f["_valor"] is not None else f["valor_cop"]
        lineas.append(f"| {f['id']} | {f['fecha']} | {f['categoria']} | {valor} | {veredicto} | {motivo} |")

    assert sum(cuenta.values()) == len(filas), "Los conteos no cuadran"

    informe = Template(PLANTILLA.read_text(encoding="utf-8")).substitute(
        legalizacion=primera["legalizacion"],
        empleado=primera["empleado"],
        ciudad=primera["ciudad"],
        grupo=grupo,
        salida=primera["salida"],
        regreso=primera["regreso"],
        filas="\n".join(lineas),
        presentados=len(filas),
        aprobados=cuenta["Aprobado"],
        rechazados=cuenta["Rechazado"],
        devueltos=cuenta["Devuelto"],
        total=pesos(total),
    )
    sys.stdout.reconfigure(encoding="utf-8")
    print(informe)


if __name__ == "__main__":
    main()
