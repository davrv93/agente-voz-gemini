# Prompt 3 · Entender un audio

```text
Crea la función entender(wav_bytes) que mande un audio WAV a gemini-3.5-flash-lite (generateContent)
y devuelva un JSON.
- El audio va como parte inlineData {mimeType: "audio/wav", data: base64}, junto a la instrucción
  «Transcribe el audio tal cual y clasifícalo».
- generationConfig: responseMimeType "application/json", temperature 0 y un responseSchema con:
  transcripcion (string), idioma (string), intencion (enum: consulta_producto, precio, horario,
  delivery, reclamo, saludo, otro), emocion (enum: tranquilo, contento, apurado, molesto, preocupado),
  productos (array de string) y urgente (boolean). Todos obligatorios.
- Si Google responde 500/502/503/504, reintenta 2 veces esperando 2 y 4 segundos; si sigue,
  usa gemini-3.1-flash-lite.
- Muestra también usageMetadata (tokens de entrada y salida).
```
