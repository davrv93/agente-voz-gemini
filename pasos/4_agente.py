"""Paso 4 · El agente completo: escuchar (Flash-Lite) → pensar (Flash-Lite) → hablar (Flash TTS).
Uso: docker compose run --rm agente python pasos/4_agente.py [ejemplos/archivo.wav]"""
import json
import sys
import time
from pathlib import Path
from _comun import RAIZ, gemini, guardar, imprimir_json, mostrar

ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "ejemplos" / "1-cliente-paracetamol.wav"
botica = json.loads((RAIZ / "app" / "botica.json").read_text(encoding="utf-8"))
t0 = time.time()
print("1 · ESCUCHAR")
entendio, i1 = gemini.entender(ruta.read_bytes()); mostrar(i1); imprimir_json(entendio)
print("\n2 · PENSAR")
decidio, i2 = gemini.pensar(entendio, botica); mostrar(i2); imprimir_json(decidio)
print("\n3 · HABLAR")
wav, i3 = gemini.hablar(decidio["respuesta"], "Sulafat", decidio["estilo"]); mostrar(i3)
guardar("paso4-respuesta.wav", wav)
print(f"\nTotal: {time.time() - t0:.1f} s")
