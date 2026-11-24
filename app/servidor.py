"""Servidor del agente de voz. Sirve la página y hace de puente con Gemini.

La llave de Gemini solo vive aquí (variable GEMINI_API_KEY). El navegador nunca la ve.
Rutas:
  GET  /                 la página (app/web/index.html)
  GET  /api/estado       modelos configurados y si hay llave (sí/no, nunca la llave)
  POST /api/hablar       {texto, voz, estilo}                     → {audio, info}
  POST /api/dialogo      {lineas:[{personaje,texto,estilo}], voces} → {audio, info}
  POST /api/entender     {audio}  (WAV en base64)                  → {entendio, info}
  POST /api/agente       {audio, historial}                        → {entendio, decidio, audio, pasos}
"""
import base64
import json
import os
import struct
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gemini  # noqa: E402

RAIZ = Path(__file__).parent
WEB = RAIZ / "web"
SALIDA = Path(os.environ.get("SALIDA", RAIZ.parent / "salida"))
BOTICA = json.loads((RAIZ / "botica.json").read_text(encoding="utf-8"))
MAX_CUERPO = 8 * 1024 * 1024          # 8 MB por pedido
MAX_SEGUNDOS = 60                      # audio de entrada: hasta 1 minuto
MAX_TEXTO = 600                        # caracteres para convertir en voz
LIMITE = int(os.environ.get("LIMITE_POR_HORA", "60"))   # pedidos a Gemini por IP y por hora
VOCES = ["Kore", "Puck", "Charon", "Sulafat", "Achird", "Aoede", "Leda", "Orus", "Gacrux", "Vindemiatrix"]

_cuenta, _candado = {}, threading.Lock()


def _permitido(ip):
    ahora = time.time()
    with _candado:
        lista = [t for t in _cuenta.get(ip, []) if ahora - t < 3600]
        if len(lista) >= LIMITE:
            _cuenta[ip] = lista
            return False
        lista.append(ahora)
        _cuenta[ip] = lista
        return True


def _segundos_wav(b):
    """Duración de un WAV PCM leyendo su cabecera. Lanza ValueError si no es WAV."""
    if len(b) < 44 or b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        raise ValueError("El audio debe llegar como WAV (la página lo convierte sola).")
    i, tasa_bytes, datos = 12, 0, 0
    while i + 8 <= len(b):
        cid, tam = b[i:i + 4], struct.unpack("<I", b[i + 4:i + 8])[0]
        if cid == b"fmt ":
            tasa_bytes = struct.unpack("<I", b[i + 16:i + 20])[0]
        elif cid == b"data":
            datos = min(tam, len(b) - i - 8)
            break
        i += 8 + tam + (tam & 1)
    if not tasa_bytes:
        raise ValueError("WAV sin cabecera de formato.")
    return datos / tasa_bytes


def _guardar(nombre, wav):
    try:
        SALIDA.mkdir(parents=True, exist_ok=True)
        (SALIDA / nombre).write_bytes(wav)
    except OSError:
        pass   # guardar una copia es opcional


class Manejador(BaseHTTPRequestHandler):
    server_version = "agente-voz"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _json(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path == "/api/estado":
            return self._json(200, {"modelo_voz": gemini.MODELO_VOZ, "respaldo_voz": gemini.MODELO_VOZ_RESPALDO,
                                    "modelo_oido": gemini.MODELO_OIDO, "voces": VOCES,
                                    "hay_llave": bool(os.environ.get("GEMINI_API_KEY", "").strip()
                                                      and not os.environ["GEMINI_API_KEY"].startswith("pega-")),
                                    "negocio": BOTICA["negocio"]})
        ruta = "index.html" if self.path in ("/", "/index.html") else self.path.lstrip("/").split("?")[0]
        archivo = (WEB / ruta).resolve()
        if WEB.resolve() not in archivo.parents or not archivo.is_file():
            return self._json(404, {"error": "No existe"})
        tipo = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
                ".svg": "image/svg+xml"}.get(archivo.suffix, "application/octet-stream")
        cuerpo = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "script-src 'self' 'unsafe-inline'; media-src 'self' blob: data:; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > MAX_CUERPO:
            return self._json(413, {"error": "El pedido pasa de 8 MB."})
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except ValueError:
            return self._json(400, {"error": "JSON inválido"})
        if not _permitido(self.client_address[0]):
            return self._json(429, {"error": f"Llegaste al tope de {LIMITE} pedidos por hora (LIMITE_POR_HORA)."})
        try:
            if self.path == "/api/hablar":
                return self._hablar(datos)
            if self.path == "/api/dialogo":
                return self._dialogo(datos)
            if self.path == "/api/entender":
                wav = self._audio(datos)
                entendio, info = gemini.entender(wav)
                return self._json(200, {"entendio": entendio, "info": info})
            if self.path == "/api/agente":
                return self._agente(datos)
            return self._json(404, {"error": "No existe"})
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except gemini.ErrorGemini as e:
            return self._json(e.codigo if 400 <= e.codigo < 600 else 502, {"error": str(e)})

    def _audio(self, datos):
        try:
            wav = base64.b64decode(datos.get("audio", ""), validate=True)
        except ValueError:
            raise ValueError("El audio no está en base64.") from None
        s = _segundos_wav(wav)
        if s > MAX_SEGUNDOS:
            raise ValueError(f"El audio dura {s:.0f} s; el máximo es {MAX_SEGUNDOS} s.")
        return wav

    def _hablar(self, d):
        texto = str(d.get("texto", "")).strip()
        if not texto or len(texto) > MAX_TEXTO:
            raise ValueError(f"Escribe entre 1 y {MAX_TEXTO} caracteres.")
        voz = d.get("voz") if d.get("voz") in VOCES else "Kore"
        wav, info = gemini.hablar(texto, voz, str(d.get("estilo", ""))[:120])
        _guardar(f"hablar-{int(time.time())}.wav", wav)
        return self._json(200, {"audio": base64.b64encode(wav).decode(), "info": info})

    def _dialogo(self, d):
        voces = {str(k)[:30]: v for k, v in (d.get("voces") or {}).items() if v in VOCES}
        lineas = [(str(l.get("personaje", ""))[:30], str(l.get("texto", ""))[:300], str(l.get("estilo", ""))[:80])
                  for l in (d.get("lineas") or [])[:12]]
        if len(voces) != 2 or not lineas or any(p not in voces or not t for p, t, _ in lineas):
            raise ValueError("Un diálogo lleva exactamente 2 personajes, cada uno con su voz, y cada línea con texto.")
        wav, info = gemini.dialogo(lineas, voces)
        _guardar(f"dialogo-{int(time.time())}.wav", wav)
        return self._json(200, {"audio": base64.b64encode(wav).decode(), "info": info})

    def _agente(self, d):
        wav = self._audio(d)
        historial = [{"quien": str(h.get("quien", ""))[:10], "texto": str(h.get("texto", ""))[:400]}
                     for h in (d.get("historial") or [])[-6:]]
        t0 = time.time()
        entendio, i1 = gemini.entender(wav)                       # 1. escuchar  (Flash-Lite)
        decidio, i2 = gemini.pensar(entendio, BOTICA, historial)  # 2. pensar    (Flash-Lite)
        voz, i3 = gemini.hablar(decidio["respuesta"], d.get("voz") if d.get("voz") in VOCES else "Sulafat",
                                decidio.get("estilo", "")[:80])   # 3. hablar    (Flash TTS)
        _guardar(f"agente-{int(time.time())}.wav", voz)
        return self._json(200, {"entendio": entendio, "decidio": decidio,
                                "audio": base64.b64encode(voz).decode(),
                                "pasos": {"escuchar": i1, "pensar": i2, "hablar": i3},
                                "total_segundos": round(time.time() - t0, 2)})


if __name__ == "__main__":
    puerto = int(os.environ.get("PUERTO_INTERNO", "8090"))
    print(f"Agente de voz en http://127.0.0.1:{os.environ.get('PUERTO', puerto)}  "
          f"(voz {gemini.MODELO_VOZ}, oído {gemini.MODELO_OIDO})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", puerto), Manejador).serve_forever()
