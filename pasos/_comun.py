"""Ayudas compartidas por los pasos: importa el cliente de app/ y guarda los audios en salida/."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
import gemini  # noqa: E402,F401

SALIDA = RAIZ / "salida"
SALIDA.mkdir(exist_ok=True)


def guardar(nombre, wav):
    ruta = SALIDA / nombre
    ruta.write_bytes(wav)
    print(f"Audio guardado en salida/{nombre} ({len(wav) // 1024} KB). Ábrelo con doble clic.")


def mostrar(info):
    print(f"[{info['modelo']} · {info['segundos']} s · {info['tokens_entrada']} tokens de entrada, "
          f"{info['tokens_salida']} de salida]")


def imprimir_json(d):
    print(json.dumps(d, ensure_ascii=False, indent=2))


def _error_amable(tipo, valor, tb):
    """Muestra los errores de Gemini en una línea, sin la traza completa."""
    if isinstance(valor, gemini.ErrorGemini):
        consejo = {429: "Se acabó la cuota de ese modelo por ahora: espera o cambia el modelo en .env.",
                   503: "Google está saturado en este momento: vuelve a intentarlo en un minuto.",
                   500: "Falta la llave o algo falló en el servidor de Google.",
                   400: "El pedido no es válido: revisa el texto o el audio."}.get(valor.codigo, "")
        print(f"Error {valor.codigo} · {valor}\n{consejo}", file=sys.stderr)
        sys.exit(1)
    sys.__excepthook__(tipo, valor, tb)


sys.excepthook = _error_amable
