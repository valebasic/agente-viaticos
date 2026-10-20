import os
import threading
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
CARPETA_PROMPT = Path(__file__).parent / "prompt"
CARPETA_CONOCIMIENTO = Path(__file__).parent / "conocimiento"
INSTRUCCIONES = (CARPETA_PROMPT / "sistema.md").read_text(encoding="utf-8")

for archivo in sorted(CARPETA_CONOCIMIENTO.iterdir()):
    if archivo.is_file():
        contenido = archivo.read_text(encoding="utf-8")
        INSTRUCCIONES += f'\n\n<documento nombre="{archivo.name}">\n{contenido}\n</documento>'

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ultima_interaccion = None


def consultar(pregunta):
    global ultima_interaccion
    interaccion = client.interactions.create(
        model=MODELO,
        system_instruction=INSTRUCCIONES,
        input=pregunta,
        previous_interaction_id=ultima_interaccion,
    )
    ultima_interaccion = interaccion.id
    return interaccion.output_text


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
