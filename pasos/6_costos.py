"""Paso 6 · Cuántos tokens cuesta un audio antes de mandarlo (countTokens no genera nada).
Uso: docker compose run --rm agente python pasos/6_costos.py [ejemplos/archivo.wav]"""
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path
from _comun import RAIZ, gemini

ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "ejemplos" / "1-cliente-paracetamol.wav"
wav = ruta.read_bytes()
cuerpo = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wav).decode()}}]}]}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{gemini.MODELO_OIDO}:countTokens",
                             data=json.dumps(cuerpo).encode(),
                             headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"})
tokens = json.load(urllib.request.urlopen(req, timeout=60))["totalTokens"]
import wave, io
with wave.open(io.BytesIO(wav)) as w:
    seg = w.getnframes() / w.getframerate()
print(f"{ruta.name}: {seg:.1f} s de audio → {tokens} tokens ({tokens / seg:.0f} por segundo; la documentación dice 32)")
print(f"Un minuto de audio ≈ {round(tokens / seg * 60)} tokens. Precios vigentes: https://ai.google.dev/gemini-api/docs/pricing")
