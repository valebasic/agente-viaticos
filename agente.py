import os
import sys

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
INSTRUCCIONES = "Responde siempre en español, actua como un cavernicola."

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

pregunta = " ".join(sys.argv[1:]) or input("Pregunta: ")

interaccion = client.interactions.create(
    model=MODELO,
    system_instruction=INSTRUCCIONES,
    input=pregunta,
)
print(interaccion.output_text)
