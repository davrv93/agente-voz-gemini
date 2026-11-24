# Prompt 1 · Texto a voz

Pégalo en tu asistente de IA (Claude, DeepSeek, ChatGPT…) dentro de una carpeta vacía.

```text
Crea un script en Python 3.12, solo con la biblioteca estándar (urllib, json, base64), que convierta
un texto en voz con la API de Gemini.
- Modelo: gemini-3.8-flash-tts, endpoint POST
  https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent
- Llave en la cabecera x-goog-api-key, leída de la variable de entorno GEMINI_API_KEY.
  Nunca la escribas en el código ni la imprimas.
- generationConfig: responseModalities ["AUDIO"] y speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName = "Sulafat".
- El estilo («cálido y tranquilo») va en la parte del texto como speechMetadata.style, para que no se lea en voz alta.
- La respuesta trae el audio en candidates[0].content.parts[0].inlineData.data (base64, WAV de 24 kHz).
  Guárdalo como salida/hola.wav.
- Si la API responde 429 (cuota), reintenta con gemini-3.8-flash-lite-tts.
Explícame cada parte en 1 línea.
```
