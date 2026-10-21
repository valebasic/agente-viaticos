import csv
import json
import os
import re
import time
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

MODELO = "gemini-3.5-flash-lite"
CARPETA = Path(__file__).parent
ARCHIVO_GASTOS = CARPETA / "conocimiento" / "gastos.csv"
ARCHIVO_REPORTE = CARPETA / "reporte.md"

# Política de viáticos v2.0 (prevalece sobre las preguntas frecuentes).
TOPE_ALIMENTACION_DIA = 95_000
TOPE_TRANSPORTE_DIA = 60_000
TOPE_HOSPEDAJE_NOCHE = {"A": 320_000, "B": 240_000}
CIUDADES_GRUPO_A = {"bogota", "medellin", "cartagena"}
UMBRAL_DIRECTOR = 1_500_000

ETIQUETAS = {
    "normal": None,
    "alcohol": "bebidas alcohólicas no son reembolsables",
    "propina": "las propinas no son reembolsables",
    "minibar": "el minibar no es reembolsable",
    "multa": "las multas y comparendos no son reembolsables",
    "entretenimiento": "el entretenimiento personal no es reembolsable",
    "acompanante": "los gastos de acompañantes no son reembolsables",
    "tiquete_ultimo_momento": "tiquete comprado sin los 7 días de anticipación o por cuenta propia",
    "lavanderia": "lavandería: solo se reembolsa en viajes de 5 noches o más, requiere revisión manual",
}

MAX_REINTENTOS = 5
ESPERA_INICIAL = 15

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def normalizar(texto):
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").casefold().strip()


def pesos(valor):
    return f"${valor:,.0f}".replace(",", ".") + " COP"


# ---------- Código: limpiar, separar duplicadas, decidir ----------

def limpiar(ruta):
    gastos, descartadas = [], []
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            fila = {k.strip(): (v or "").strip() for k, v in fila.items()}
            try:
                fila["valor_cop"] = int(re.sub(r"\D", "", fila["valor_cop"]))
                date.fromisoformat(fila["fecha"])
            except ValueError:
                descartadas.append(fila)
                continue
            gastos.append(fila)
    return gastos, descartadas


def separar_duplicadas(gastos):
    vistos, unicos, duplicadas = {}, [], []
    for g in gastos:
        clave = tuple(normalizar(str(g[c])) for c in ("fecha", "empleado", "ciudad", "categoria", "descripcion", "valor_cop"))
        if clave in vistos:
            duplicadas.append({**g, "duplicado_de": vistos[clave]})
        else:
            vistos[clave] = g["id"]
            unicos.append(g)
    return unicos, duplicadas


def decidir(gastos, clasificacion):
    por_dia = defaultdict(int)
    for g in gastos:
        por_dia[(normalizar(g["empleado"]), g["fecha"], normalizar(g["categoria"]))] += g["valor_cop"]

    for g in gastos:
        categoria = normalizar(g["categoria"])
        etiqueta = clasificacion.get(g["descripcion"], "sin_clasificar")
        gasto_dia = por_dia[(normalizar(g["empleado"]), g["fecha"], categoria)]
        decision, motivo = "Aprobar", "Cumple la política."

        if etiqueta == "sin_clasificar":
            decision, motivo = "Pendiente", "No se pudo clasificar la descripción; requiere revisión manual."
        elif etiqueta == "lavanderia":
            decision, motivo = "Pendiente", ETIQUETAS[etiqueta].capitalize() + "."
        elif etiqueta != "normal":
            decision, motivo = "Rechazar", ETIQUETAS[etiqueta].capitalize() + "."
        elif categoria == "alimentacion" and gasto_dia > TOPE_ALIMENTACION_DIA:
            decision, motivo = "Rechazar", f"Alimentación del día ({pesos(gasto_dia)}) supera el tope de {pesos(TOPE_ALIMENTACION_DIA)}."
        elif categoria == "transporte terrestre" and gasto_dia > TOPE_TRANSPORTE_DIA:
            decision, motivo = "Rechazar", f"Transporte del día ({pesos(gasto_dia)}) supera el tope de {pesos(TOPE_TRANSPORTE_DIA)}."
        elif categoria == "hospedaje":
            grupo = "A" if normalizar(g["ciudad"]) in CIUDADES_GRUPO_A else "B"
            tope = TOPE_HOSPEDAJE_NOCHE[grupo]
            if g["valor_cop"] > tope:
                decision, motivo = "Rechazar", f"Hospedaje en {g['ciudad']} (grupo {grupo}) supera el tope de {pesos(tope)} por noche."

        if decision == "Aprobar" and g["valor_cop"] > UMBRAL_DIRECTOR:
            decision, motivo = "Pendiente", f"Supera {pesos(UMBRAL_DIRECTOR)}; requiere aprobación del director del área."

        g["etiqueta"], g["decision"], g["motivo"] = etiqueta, decision, motivo
    return gastos


# ---------- Gemini: clasificar (1 llamada) y redactar (1 llamada) ----------

def llamar_gemini(instrucciones, entrada):
    for intento in range(MAX_REINTENTOS + 1):
        try:
            interaccion = client.interactions.create(
                model=MODELO,
                system_instruction=instrucciones,
                input=entrada,
            )
            return interaccion.output_text
        except errors.APIError as error:
            if error.code != 429 or intento == MAX_REINTENTOS:
                raise
            espera = ESPERA_INICIAL * 2 ** intento
            print(f"Error 429: espero {espera} s y reintento ({intento + 1}/{MAX_REINTENTOS})...")
            time.sleep(espera)


def extraer_json(texto):
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    return json.loads(texto)


def clasificar_descripciones(gastos):
    descripciones = sorted({g["descripcion"] for g in gastos})
    instrucciones = (
        "Clasificas descripciones de gastos de viaje. Responde solo con un objeto JSON, sin texto adicional, "
        "cuyas claves sean las descripciones recibidas, escritas exactamente igual, y cuyos valores sean una "
        f"de estas etiquetas: {', '.join(ETIQUETAS)}. "
        "Usa 'normal' si el gasto no encaja en ninguna otra etiqueta. "
        "Usa 'tiquete_ultimo_momento' solo si la descripción indica compra de último momento o por cuenta propia."
    )
    respuesta = extraer_json(llamar_gemini(instrucciones, json.dumps(descripciones, ensure_ascii=False)))
    return {d: respuesta.get(d, "sin_clasificar") if respuesta.get(d) in ETIQUETAS else "sin_clasificar" for d in descripciones}


def redactar_mensajes(gastos):
    por_empleado = defaultdict(list)
    for g in gastos:
        por_empleado[g["empleado"]].append(g)
    resumen = []
    for empleado, filas in por_empleado.items():
        resumen.append({
            "empleado": empleado,
            "gastos_aprobados": sum(1 for g in filas if g["decision"] == "Aprobar"),
            "gastos_con_observaciones": [
                {"id": g["id"], "descripcion": g["descripcion"], "valor": pesos(g["valor_cop"]), "decision": g["decision"], "motivo": g["motivo"]}
                for g in filas if g["decision"] != "Aprobar"
            ],
        })
    instrucciones = (
        "Redactas mensajes de Altiplano S.A.S. para empleados sobre sus gastos de viaje. Responde solo con un objeto "
        "JSON, sin texto adicional, cuyas claves sean los nombres de empleado recibidos y cuyos valores sean el mensaje. "
        "Cada mensaje: español, tono cordial y directo, máximo cuatro frases, que mencione los id de los gastos con "
        "observaciones y su motivo, e indique que es una decisión preliminar sujeta a la aprobación del jefe inmediato. "
        "No inventes datos ni motivos distintos a los recibidos. Si no hay observaciones, informa que todos sus gastos cumplen."
    )
    respuesta = extraer_json(llamar_gemini(instrucciones, json.dumps(resumen, ensure_ascii=False)))
    return {e: respuesta.get(e, "(sin mensaje generado)") for e in por_empleado}


# ---------- Salida ----------

def escribir_reporte(descartadas, gastos, duplicadas, mensajes, linea_totales):
    lineas = ["# Reporte de procesamiento de gastos", "", f"Generado el {date.today().isoformat()}.", "", f"**{linea_totales}**", ""]

    lineas += ["## Duplicadas separadas", ""]
    if duplicadas:
        lineas += ["| Id | Duplicado de | Empleado | Fecha | Descripción | Valor |", "|---|---|---|---|---|---|"]
        lineas += [f"| {d['id']} | {d['duplicado_de']} | {d['empleado']} | {d['fecha']} | {d['descripcion']} | {pesos(d['valor_cop'])} |" for d in duplicadas]
    else:
        lineas.append("Ninguna.")

    if descartadas:
        lineas += ["", "## Filas descartadas por datos inválidos", ""]
        lineas += [f"- {d.get('id', '?')}: valor_cop={d.get('valor_cop')!r}, fecha={d.get('fecha')!r}" for d in descartadas]

    lineas += ["", "## Decisiones", "", "| Id | Empleado | Categoría | Valor | Decisión | Motivo |", "|---|---|---|---|---|---|"]
    lineas += [f"| {g['id']} | {g['empleado']} | {g['categoria']} | {pesos(g['valor_cop'])} | {g['decision']} | {g['motivo']} |" for g in gastos]

    lineas += ["", "## Mensajes a empleados", ""]
    for empleado, mensaje in mensajes.items():
        lineas += [f"**{empleado}:** {mensaje}", ""]

    ARCHIVO_REPORTE.write_text("\n".join(lineas), encoding="utf-8")


def main():
    gastos, descartadas = limpiar(ARCHIVO_GASTOS)
    leidas = len(gastos) + len(descartadas)
    gastos, duplicadas = separar_duplicadas(gastos)

    clasificacion = clasificar_descripciones(gastos)
    gastos = decidir(gastos, clasificacion)
    mensajes = redactar_mensajes(gastos)

    totales = {d: (sum(1 for g in gastos if g["decision"] == d), sum(g["valor_cop"] for g in gastos if g["decision"] == d))
               for d in ("Aprobar", "Pendiente", "Rechazar")}
    linea_totales = (
        f"Totales: {leidas} leídas | {len(descartadas)} descartadas | {len(duplicadas)} duplicadas | "
        + " | ".join(f"{d} {n} ({pesos(v)})" for d, (n, v) in totales.items())
    )

    escribir_reporte(descartadas, gastos, duplicadas, mensajes, linea_totales)
    print(linea_totales)


if __name__ == "__main__":
    main()
