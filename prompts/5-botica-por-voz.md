# Prompt 5 · La página de la botica

```text
Crea un servidor en Python (http.server, sin dependencias) y una página HTML de un solo archivo.
- La página graba el micrófono con MediaRecorder o acepta un archivo de audio (también .ogg de WhatsApp)
  y lo convierte en el navegador a WAV mono de 16 kHz con OfflineAudioContext.
- Lo manda en base64 a POST /api/agente junto con el historial de la conversación.
- El servidor corre escuchar → pensar → hablar y devuelve el JSON de cada etapa y el audio.
- La página muestra la conversación como un chat (cliente a la derecha, agente a la izquierda),
  reproduce la respuesta y guarda el historial para la siguiente pregunta.
- La llave GEMINI_API_KEY solo vive en el servidor: nunca en el HTML ni en el JavaScript.
- Límites del servidor: 8 MB por pedido, 60 s de audio, 600 caracteres de texto,
  60 pedidos por hora por IP.
- Empaquétalo con un Dockerfile (python:3.12-slim, usuario sin privilegios) y un docker-compose.yml
  que publique solo en 127.0.0.1.
```
