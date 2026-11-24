"""Paso 2 · Dos personajes con dos voces en una sola llamada (máximo 2 por pedido).
Uso: docker compose run --rm agente python pasos/2_dialogo.py"""
from _comun import gemini, guardar, mostrar

lineas = [
    ("Cliente", "Hola, ¿hacen delivery a Surco?", "curioso"),
    ("Boticaria", "Sí, de ocho de la mañana a nueve y media de la noche. <short pause> Y es gratis desde cincuenta soles.", "amable y segura"),
    ("Cliente", "<laugh> Perfecto, entonces pido ahora.", "contento"),
]
voces = {"Cliente": "Puck", "Boticaria": "Kore"}
wav, info = gemini.dialogo(lineas, voces)
mostrar(info)
guardar("paso2-dialogo.wav", wav)
