import csv
import json
import os
import threading
import tkinter as tk
import unicodedata
from datetime import date
from pathlib import Path
from tkinter import scrolledtext

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
CARPETA_PROMPT = Path(__file__).parent / "prompt"
CARPETA_CONOCIMIENTO = Path(__file__).parent / "conocimiento"
ARCHIVO_GASTOS = CARPETA_CONOCIMIENTO / "gastos.csv"
ARCHIVO_SOLICITUDES = Path(__file__).parent / "solicitudes.csv"
CAMPOS_SOLICITUDES = ["radicado", "fecha_solicitud", "empleado", "ciudad", "fecha_salida", "noches", "motivo", "estado"]
MAX_VUELTAS = 5
INSTRUCCIONES = (CARPETA_PROMPT / "sistema.md").read_text(encoding="utf-8")

for archivo in sorted(CARPETA_CONOCIMIENTO.iterdir()):
    if archivo.is_file() and archivo.suffix == ".md":
        contenido = archivo.read_text(encoding="utf-8")
        INSTRUCCIONES += f'\n\n<documento nombre="{archivo.name}">\n{contenido}\n</documento>'

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def normalizar(texto):
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").casefold().strip()


def sumar_gastos(area=None, estado=None):
    filas = 0
    total = 0
    with open(ARCHIVO_GASTOS, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if area and normalizar(fila["area"]) != normalizar(area):
                continue
            if estado and normalizar(fila["estado"]) != normalizar(estado):
                continue
            filas += 1
            total += int(fila["valor_cop"])
    return {"filas": filas, "total_cop": total}


def registrar_solicitud(empleado, ciudad, fecha_salida, noches, motivo):
    radicados = 0
    if ARCHIVO_SOLICITUDES.exists():
        with open(ARCHIVO_SOLICITUDES, encoding="utf-8", newline="") as f:
            radicados = sum(1 for _ in csv.DictReader(f))
    radicado = f"S-{radicados + 1:03d}"
    nuevo = not ARCHIVO_SOLICITUDES.exists()
    with open(ARCHIVO_SOLICITUDES, "a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SOLICITUDES)
        if nuevo:
            escritor.writeheader()
        escritor.writerow({
            "radicado": radicado,
            "fecha_solicitud": date.today().isoformat(),
            "empleado": empleado,
            "ciudad": ciudad,
            "fecha_salida": fecha_salida,
            "noches": noches,
            "motivo": motivo,
            "estado": "Pendiente de aprobación del jefe inmediato",
        })
    return {"radicado": radicado}


FUNCIONES = {"sumar_gastos": sumar_gastos, "registrar_solicitud": registrar_solicitud}

HERRAMIENTAS = [
    {
        "type": "function",
        "name": "sumar_gastos",
        "description": (
            "Cuenta y suma, con código, los gastos registrados en gastos.csv. Úsala siempre que el usuario "
            "pregunte por totales, sumas o cantidad de gastos registrados, con o sin filtro por área o estado. "
            "No la uses para registrar solicitudes ni para preguntas sobre la política."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "Área a filtrar, por ejemplo Ventas u Operaciones. Omítelo para incluir todas las áreas.",
                },
                "estado": {
                    "type": "string",
                    "description": "Estado a filtrar: Aprobado, Pendiente o Rechazado. Omítelo para incluir todos los estados.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "registrar_solicitud",
        "description": (
            "Registra una solicitud de viaje y devuelve su radicado. Úsala solo cuando el usuario pida "
            "registrar o radicar una solicitud de viaje y ya hayas confirmado los cinco datos. "
            "Si falta alguno, pídelo antes de llamarla; no inventes datos."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "empleado": {"type": "string", "description": "Nombre completo del empleado que viaja."},
                "ciudad": {"type": "string", "description": "Ciudad de destino del viaje."},
                "fecha_salida": {"type": "string", "description": "Fecha de salida en formato AAAA-MM-DD."},
                "noches": {"type": "integer", "description": "Número de noches del viaje."},
                "motivo": {"type": "string", "description": "Motivo del viaje de trabajo."},
            },
            "required": ["empleado", "ciudad", "fecha_salida", "noches", "motivo"],
        },
    },
]

ultima_interaccion = None


def consultar(pregunta):
    global ultima_interaccion
    entrada_modelo = pregunta
    for vuelta in range(MAX_VUELTAS + 1):
        interaccion = client.interactions.create(
            model=MODELO,
            system_instruction=INSTRUCCIONES,
            input=entrada_modelo,
            tools=HERRAMIENTAS,
            previous_interaction_id=ultima_interaccion,
        )
        ultima_interaccion = interaccion.id
        llamadas = [paso for paso in interaccion.steps if paso.type == "function_call"]
        if not llamadas:
            return interaccion.output_text
        if vuelta == MAX_VUELTAS:
            break
        resultados = []
        for llamada in llamadas:
            argumentos = dict(llamada.arguments)
            try:
                resultado = FUNCIONES[llamada.name](**argumentos)
            except Exception as error:
                resultado = {"error": str(error)}
            print(f"[herramienta] {llamada.name}({argumentos}) -> {resultado}")
            resultados.append({
                "type": "function_result",
                "name": llamada.name,
                "call_id": llamada.id,
                "result": [{"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}],
            })
        entrada_modelo = resultados
    return "No pude completar la consulta: se superó el máximo de 5 vueltas con herramientas."


def mostrar(autor, texto):
    chat.config(state="normal")
    chat.insert("end", f"{autor}: {texto}\n\n")
    chat.config(state="disabled")
    chat.see("end")


def responder(pregunta):
    try:
        respuesta = consultar(pregunta)
    except Exception as error:
        respuesta = f"Error: {error}"
    ventana.after(0, lambda: (mostrar("Asistente", respuesta), boton.config(state="normal")))


def enviar(_evento=None):
    pregunta = entrada.get().strip()
    if not pregunta or boton["state"] == "disabled":
        return
    entrada.delete(0, "end")
    mostrar("Tú", pregunta)
    boton.config(state="disabled")
    threading.Thread(target=responder, args=(pregunta,), daemon=True).start()


ventana = tk.Tk()
ventana.title("Asistente de viáticos")
ventana.geometry("520x600")

chat = scrolledtext.ScrolledText(ventana, wrap="word", state="disabled", font=("Segoe UI", 10))
chat.pack(fill="both", expand=True, padx=8, pady=8)

barra = tk.Frame(ventana)
barra.pack(fill="x", padx=8, pady=(0, 8))
entrada = tk.Entry(barra, font=("Segoe UI", 10))
entrada.pack(side="left", fill="x", expand=True)
entrada.bind("<Return>", enviar)
boton = tk.Button(barra, text="Enviar", command=enviar)
boton.pack(side="left", padx=(6, 0))
entrada.focus()

ventana.mainloop()
