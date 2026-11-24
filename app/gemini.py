"""Cliente mínimo de la API de Gemini, solo con la biblioteca estándar de Python.

Tres funciones, una por cada cosa que hace el agente:
  hablar()    texto → voz (WAV)     con Gemini Flash TTS
  entender()  voz → JSON            con Gemini Flash-Lite (transcripción, intención, emoción)
  pensar()    JSON → respuesta      con Gemini Flash-Lite (decide qué contestar)

La llave se lee de la variable de entorno GEMINI_API_KEY (archivo .env). Nunca se imprime
ni se manda al navegador: el navegador habla con este servidor y este servidor con Google.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
MODELO_VOZ = os.environ.get("MODELO_VOZ", "gemini-3.8-flash-tts")
MODELO_VOZ_RESPALDO = os.environ.get("MODELO_VOZ_RESPALDO", "gemini-3.8-flash-lite-tts")
MODELO_OIDO = os.environ.get("MODELO_OIDO", "gemini-3.5-flash-lite")
MODELO_OIDO_RESPALDO = os.environ.get("MODELO_OIDO_RESPALDO", "gemini-3.1-flash-lite")
REINTENTABLES = {500, 502, 503, 504}   # «alta demanda» y fallas pasajeras de Google


class ErrorGemini(Exception):
    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo


def _llave():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k or k.startswith("pega-"):
        raise ErrorGemini(500, "Falta GEMINI_API_KEY en el archivo .env")
    return k


def _llamar(modelo, cuerpo, intentos=3):
    """Hace la llamada; si Google responde 5xx (sobrecarga pasajera) espera y reintenta."""
    for n in range(intentos):
        try:
            return _llamar_una_vez(modelo, cuerpo)
        except ErrorGemini as e:
            if e.codigo not in REINTENTABLES or n == intentos - 1:
                raise
            time.sleep(2 * (n + 1))


def _llamar_una_vez(modelo, cuerpo):
    req = urllib.request.Request(API.format(modelo), data=json.dumps(cuerpo).encode(),
                                 headers={"x-goog-api-key": _llave(), "Content-Type": "application/json"})
    t = time.time()
    try:
        d = json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e)["error"]["message"]
        except Exception:
            msg = e.reason
        raise ErrorGemini(e.code, f"{modelo}: {msg}") from None
    uso = d.get("usageMetadata", {})
    return d, {"modelo": modelo, "segundos": round(time.time() - t, 2),
               "tokens_entrada": uso.get("promptTokenCount", 0),
               "tokens_salida": uso.get("candidatesTokenCount", 0)}


def _con_respaldo(cuerpo, modelo, respaldo):
    """Primero el modelo principal; si se acabó la cuota (429) o sigue saturado (5xx), el de respaldo."""
    try:
        return _llamar(modelo, cuerpo)
    except ErrorGemini as e:
        if (e.codigo != 429 and e.codigo not in REINTENTABLES) or not respaldo:
            raise
        return _llamar(respaldo, cuerpo)


def _audio(d):
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            return base64.b64decode(p["inlineData"]["data"])
    raise ErrorGemini(502, "La respuesta no trajo audio")


def hablar(texto, voz="Kore", estilo=""):
    """Texto → WAV (24 kHz, mono, 16 bits). El estilo va aparte del texto: no se lee en voz alta."""
    parte = {"text": texto}
    if estilo:
        parte["speechMetadata"] = {"style": estilo}
    cuerpo = {"contents": [{"role": "user", "parts": [parte]}],
              "generationConfig": {"responseModalities": ["AUDIO"],
                                   "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
    d, info = _con_respaldo(cuerpo, MODELO_VOZ, MODELO_VOZ_RESPALDO)
    return _audio(d), info


def dialogo(lineas, voces):
    """lineas = [(personaje, texto, estilo)], voces = {personaje: voz}. Hasta dos personajes."""
    partes = [{"text": t, "speechMetadata": {"speaker": p, **({"style": e} if e else {})}} for p, t, e in lineas]
    cuerpo = {"contents": [{"role": "user", "parts": partes}],
              "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"multiSpeakerVoiceConfig": {
                  "speakerVoiceConfigs": [{"speaker": p, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": v}}}
                                          for p, v in voces.items()]}}}}
    d, info = _con_respaldo(cuerpo, MODELO_VOZ, MODELO_VOZ_RESPALDO)
    return _audio(d), info


ESQUEMA_OIDO = {
    "type": "OBJECT",
    "properties": {
        "transcripcion": {"type": "STRING"},
        "idioma": {"type": "STRING"},
        "intencion": {"type": "STRING", "enum": ["consulta_producto", "precio", "horario", "delivery",
                                                  "reclamo", "saludo", "otro"]},
        "emocion": {"type": "STRING", "enum": ["tranquilo", "contento", "apurado", "molesto", "preocupado"]},
        "productos": {"type": "ARRAY", "items": {"type": "STRING"}},
        "urgente": {"type": "BOOLEAN"},
    },
    "required": ["transcripcion", "idioma", "intencion", "emocion", "productos", "urgente"],
}


def entender(wav, instrucciones="Transcribe el audio tal cual y clasifícalo."):
    """Voz → JSON con la forma de ESQUEMA_OIDO, con Flash-Lite."""
    cuerpo = {"contents": [{"role": "user", "parts": [
                 {"text": instrucciones},
                 {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wav).decode()}}]}],
              "generationConfig": {"responseMimeType": "application/json", "responseSchema": ESQUEMA_OIDO,
                                   "temperature": 0}}
    d, info = _con_respaldo(cuerpo, MODELO_OIDO, MODELO_OIDO_RESPALDO)
    return json.loads(d["candidates"][0]["content"]["parts"][0]["text"]), info


ESQUEMA_RESPUESTA = {
    "type": "OBJECT",
    "properties": {
        "respuesta": {"type": "STRING"},
        "estilo": {"type": "STRING"},
        "derivar_a_humano": {"type": "BOOLEAN"},
    },
    "required": ["respuesta", "estilo", "derivar_a_humano"],
}


def pensar(lo_que_entendio, conocimiento, historial=()):
    """Decide qué contestar. Solo usa el conocimiento que le pasas: si no sabe, deriva a una persona."""
    prompt = (
        "Eres el asistente de voz de un negocio. Responde en español, en 1 o 2 frases cortas, "
        "como se habla por teléfono (sin listas ni emojis). Usa SOLO estos datos del negocio; "
        "si la respuesta no está ahí, dilo con amabilidad y marca derivar_a_humano. "
        "Si la persona está molesta o es urgente, empieza reconociéndolo. "
        "En 'estilo' describe en pocas palabras cómo debe sonar la voz.\n\n"
        f"DATOS DEL NEGOCIO:\n{json.dumps(conocimiento, ensure_ascii=False)}\n\n"
        f"CONVERSACIÓN PREVIA:\n{json.dumps(list(historial), ensure_ascii=False)}\n\n"
        f"LO QUE ACABA DE DECIR (ya transcrito y clasificado):\n{json.dumps(lo_que_entendio, ensure_ascii=False)}"
    )
    cuerpo = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
              "generationConfig": {"responseMimeType": "application/json", "responseSchema": ESQUEMA_RESPUESTA,
                                   "temperature": 0.3}}
    d, info = _con_respaldo(cuerpo, MODELO_OIDO, MODELO_OIDO_RESPALDO)
    return json.loads(d["candidates"][0]["content"]["parts"][0]["text"]), info
