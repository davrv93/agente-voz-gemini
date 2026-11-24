"""Paso 5 · Conversación de varias vueltas con la botica: el agente recuerda lo que ya se dijo.
Uso: docker compose run --rm agente python pasos/5_botica.py audio1.wav [audio2.wav ...]
Sin argumentos usa los audios de ejemplos/ en orden. Solo escucha y piensa (no gasta voz);
agrega --voz para que también responda en audio la última vuelta."""
import json
import sys
from _comun import RAIZ, gemini, guardar, mostrar

args = [a for a in sys.argv[1:] if a != "--voz"]
audios = args or sorted(str(p) for p in (RAIZ / "ejemplos").glob("*.wav"))
botica = json.loads((RAIZ / "app" / "botica.json").read_text(encoding="utf-8"))
historial = []
for n, ruta in enumerate(audios, 1):
    entendio, i1 = gemini.entender(open(ruta, "rb").read())
    decidio, i2 = gemini.pensar(entendio, botica, historial)
    print(f"\nVuelta {n} · {ruta.split('/')[-1]}")
    print(f"  Cliente  ({entendio['intencion']}, {entendio['emocion']}): {entendio['transcripcion']}")
    print(f"  Agente   {'(deriva a una persona) ' if decidio['derivar_a_humano'] else ''}{decidio['respuesta']}")
    mostrar(i1); mostrar(i2)
    historial += [{"quien": "cliente", "texto": entendio["transcripcion"]}, {"quien": "agente", "texto": decidio["respuesta"]}]
if "--voz" in sys.argv:
    wav, i3 = gemini.hablar(decidio["respuesta"], "Sulafat", decidio["estilo"]); mostrar(i3)
    guardar("paso5-ultima-respuesta.wav", wav)
