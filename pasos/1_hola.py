"""Paso 1 · Texto a voz con Gemini Flash TTS.
Uso: docker compose run --rm agente python pasos/1_hola.py "Tu frase" [Voz] [estilo]"""
import sys
from _comun import gemini, guardar, mostrar

texto = sys.argv[1] if len(sys.argv) > 1 else "Hola, soy tu asistente de voz. Hoy aprendemos a que una computadora hable con naturalidad."
voz = sys.argv[2] if len(sys.argv) > 2 else "Sulafat"
estilo = sys.argv[3] if len(sys.argv) > 3 else "cálido y tranquilo"
wav, info = gemini.hablar(texto, voz, estilo)
mostrar(info)
guardar("paso1-hola.wav", wav)
