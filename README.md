# Asistente de Voz

Aplicación de asistente de voz con múltiples personalidades que utiliza reconocimiento de voz en tiempo real y respuestas generadas por IA.

## Características

- Reconocimiento de voz en español usando Vosk
- Tres asistentes con personalidades diferentes:
  - **Camilo**: Asistente legal (usa workspace "blawd")
  - **Maia**: Asistente Odoo (usa workspace "odoo")
  - **Gael**: Asistente general (usa workspace "chat")
- Respuestas de voz naturales usando Edge TTS
- Interfaz gráfica con Flet
- Soporte para múltiples APIs (AnythingLLM, Google Gemini)

## Requisitos Previos

### Dependencias del Sistema

**Linux:**
```bash
sudo apt-get install python3-pip python3-venv portaudio19-dev mpg123
```

**macOS:**
```bash
brew install portaudio mpg123
```

**Windows:**
- No requiere dependencias adicionales del sistema

## Instalación

### 1. Crear entorno virtual (opcional pero recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias Python

```bash
pip install sounddevice vosk flet requests edge-tts
```

### 3. Descargar Modelo Vosk (ESPAÑOL)

El modelo de reconocimiento de voz debe descargarse desde el repositorio oficial de Vosk:

**URL de descarga:**
```
https://alphacephei.com/vosk/models
```

**Específicamente el modelo pequeño en español:**
```
https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
```

**Instrucciones:**
1. Descarga el archivo ZIP del modelo
2. Descomprímelo en una ubicación accesible
3. Actualiza la ruta en el script (línea 22):

```python
rutModel = r'/ruta/a/tu/vosk-model-small-es-0.42'
```

**Ruta por defecto en el script:**
```
/home/jose/desarrollo/voz_a_texto/vosk-model-small-es-0.42
```

## Configuración

### API Keys

El script incluye configuración para dos APIs:

1. **AnythingLLM API** (líneas 37-39):
   ```python
   ANYTHING_KEY = 'TU_API_KEY_AQUI'
   ```

2. **Google Gemini API** (línea 40):
   ```python
   GOOGLE_API_KEY = 'TU_GOOGLE_API_KEY_AQUI'
   ```

Para obtener API keys:
- AnythingLLM: Instala y configura tu servidor AnythingLLM local
- Google Gemini: Obtén una clave en [Google AI Studio](https://makersuite.google.com/app/apikey)

## Uso

Ejecuta la aplicación:

```bash
python main_ok.py
```

### Comandos de Voz

1. Di el nombre del asistente para activarlo:
   - "Camilo" - Asistente legal
   - "Maia" - Asistente Odoo
   - "Gael" - Asistente general

2. El asistente responderá "✅ [Nombre] activado. ¡Habla ahora!"

3. Haz tu pregunta o comando

4. El asistente responderá tanto visualmente como con voz

## Estructura de la Interfaz

- **Barra de estado**: Muestra si el sistema está esperando palabra clave o escuchando
- **Área de chat**: Historial de conversaciones con burbujas de colores por asistente
- **Panel de información**: Lista de comandos disponibles
- **Botón Limpiar**: Limpia el historial de chat

## Solución de Problemas

### Error cargando el modelo
- Verifica que la ruta del modelo sea correcta
- Asegúrate de que el modelo esté completamente descomprimido

### Error de audio
- Verifica que el micrófono esté conectado y funcionando
- En Linux, asegúrate de que tu usuario tenga permisos para el dispositivo de audio

### Error en TTS (texto a voz)
- Verifica conexión a internet (Edge TTS requiere conexión)
- Asegúrate de tener mpg123 instalado en Linux

### Error de API
- Verifica que las API keys sean válidas
- Asegúrate de que el servidor AnythingLLM esté corriendo y accesible
- Verifica tu conexión a internet

## Dependencias Principales

- **sounddevice**: Captura de audio
- **vosk**: Reconocimiento de voz offline
- **flet**: Interfaz gráfica
- **edge-tts**: Síntesis de voz natural
- **requests**: Llamadas a APIs externas
