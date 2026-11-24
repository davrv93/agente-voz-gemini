"""Paso 3 · Entender un audio con Gemini Flash-Lite: transcripción, intención y emoción en JSON.
Uso: docker compose run --rm agente python pasos/3_entender.py [ejemplos/archivo.wav]
El audio debe ser WAV. Para otros formatos usa la página (la convierte sola)."""
import sys
from pathlib import Path
from _comun import RAIZ, gemini, imprimir_json, mostrar

ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "ejemplos" / "1-cliente-paracetamol.wav"
entendio, info = gemini.entender(ruta.read_bytes())
mostrar(info)
imprimir_json(entendio)
