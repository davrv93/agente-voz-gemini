# Prompt 2 · Dos voces en una sola llamada

```text
Agrega una función dialogo(lineas, voces) al script anterior.
- lineas es una lista de (personaje, texto, estilo); voces es {personaje: voz}. Máximo 2 personajes.
- Cada línea es una parte distinta de contents con speechMetadata: {speaker, style}.
- speechConfig.multiSpeakerVoiceConfig.speakerVoiceConfigs lleva un {speaker, voiceConfig.prebuiltVoiceConfig.voiceName} por personaje.
- Prueba con un cliente (voz Puck) y una boticaria (voz Kore) hablando del delivery.
- Usa etiquetas dentro del texto como <short pause> y <laugh>.
Valida que haya exactamente 2 personajes y que cada línea tenga texto; si no, error claro en español.
```
