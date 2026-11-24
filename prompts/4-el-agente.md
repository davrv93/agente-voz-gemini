# Prompt 4 · El agente: escuchar → pensar → hablar

```text
Arma el agente en tres etapas y mide cuánto tarda cada una:
1. ESCUCHAR: entender(wav) con gemini-3.5-flash-lite → JSON.
2. PENSAR: pensar(lo_que_entendio, datos_del_negocio, historial) con gemini-3.5-flash-lite.
   Prompt: «Eres el asistente de voz de un negocio. Responde en 1 o 2 frases cortas, como se habla
   por teléfono, sin listas ni emojis. Usa SOLO los datos del negocio; si la respuesta no está ahí,
   dilo y marca derivar_a_humano. Si la persona está molesta o es urgente, empieza reconociéndolo.»
   Salida JSON: respuesta (string), estilo (string: cómo debe sonar), derivar_a_humano (boolean).
3. HABLAR: convierte la respuesta en voz con gemini-3.8-flash-tts usando el estilo que eligió el paso 2.
Los datos del negocio vienen de botica.json. Imprime el JSON de cada etapa y guarda el WAV final.
```
