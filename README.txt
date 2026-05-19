# InfoVoz AI - Asistente de Voz Inteligente

## Descripción
InfoVoz AI es un asistente de voz inteligente que combina reconocimiento de voz en español con múltiples APIs de IA para proporcionar respuestas conversacionales naturales. La aplicación permite interactuar por voz o texto con tres asistentes especializados.

## Características Principales

### 🎙️ Reconocimiento de Voz
- Reconocimiento continuo en español usando Vosk
- Activación por palabras clave: "Camilo", "Luna", "Gael"
- Palabra de parada: "alto" para detener reproducción de audio
- Indicador visual del estado del micrófono

### 🤖 Asistentes Especializados
- **Camilo**: Asistente con voz masculina profesional (español colombiano)
- **Luna**: Asistente con voz femenina cálida (español español)
- **Gael**: Asistente con voz neutra clara (español mexicano)

### 💬 Interfaces de Interacción
- **Voz**: Activación por palabras clave y respuestas habladas
- **Texto**: Campo de entrada para preguntas escritas
- **Chat**: Interfaz conversacional con historial de mensajes

### 🔐 Sistema de Autenticación
- Login seguro con usuarios y contraseñas
- Gestión de usuarios en archivo JSON
- Roles y permisos configurables

## Requisitos del Sistema

### Dependencias Principales
- Python 3.7+
- sounddevice - Captura de audio
- vosk - Reconocimiento de voz offline
- flet - Interfaz gráfica
- edge-tts - Síntesis de voz
- requests - Comunicación con APIs

### Archivos Necesarios
- Modelo Vosk: `/home/jose/desarrollo/voz_a_texto/vosk-model-small-es-0.42`
- Archivo de usuarios: `users.json` (se crea automáticamente)

### Dependencias de Audio
- **Linux**: mpg123 para reproducción MP3
- **Windows**: winsound (incluido)
- **macOS**: afplay (incluido)

## Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install sounddevice vosk flet edge-tts requests asyncio threading
```

### 2. Configurar Audio en Linux
```bash
sudo apt install mpg123
```

### 3. Descargar Modelo Vosk
Descargar modelo español pequeño desde:
https://alphacephei.com/vosk/models

### 4. Configurar APIs
Editar las siguientes variables en el código:
- `ANYTHING_KEY`: API Key para AnythingLLM
- `GOOGLE_API_KEY`: API Key para Google Gemini

## Uso

### Iniciar la Aplicación
```bash
python main.py
```

### Interacción por Voz
1. La aplicación inicia escuchando continuamente
2. Di el nombre del asistente: "Camilo", "Luna" o "Gael"
3. El sistema confirmará la activación
4. Realiza tu pregunta
5. Recibe respuesta hablada y visual

### Interacción por Texto
1. Selecciona asistente del menú desplegable
2. Escribe pregunta en campo de texto
3. Presiona Enter o clic en botón de enviar
4. Recibe respuesta visual y opcionalmente hablada

### Comandos de Voz
- **Activar**: "Camilo", "Luna", "Gael"
- **Detener audio**: "alto"
- **Preguntas**: Cualquier pregunta después de activar asistente

## Arquitectura Técnica

### Estructura Multithread
- **Thread principal**: Interfaz gráfica Flet
- **Thread audio**: Captura y procesamiento de voz
- **Thread APIs**: Comunicación asíncrona con servicios externos
- **Thread TTS**: Síntesis y reproducción de voz

### Flujo de Procesamiento
1. Audio capturado en tiempo real (16kHz)
2. Reconocimiento con VosK offline
3. Detección de palabras clave
4. Llamada a API correspondiente
5. Síntesis de voz con Edge TTS
6. Reproducción sincronizada con visualización

### Gestión de Estados
- Control de micrófono habilitado/deshabilitado
- Estados de transcripción activa/inactiva
- Indicadores visuales en tiempo real

## Personalización

### Agregar Nuevos Asistentes
1. Añadir voz en diccionario `VOCES_ASISTENTES`
2. Configurar API en función `generar_respuesta_ia_thread`
3. Actualizar palabras clave en bucle de reconocimiento

### Modificar Voces
Editar el diccionario `VOCES_ASISTENTES` con voces de Edge TTS:
```python
VOCES_ASISTENTES = {
    "nombre_asistente": "voz-edge-tts-id"
}
```

### Configurar APIs
Las funciones `llamar_api_anything_async` y `llamar_api_gemini_async` pueden adaptarse para diferentes servicios.

## Solución de Problemas

### Problemas Comunes
- **Micrófono no detecta**: Verificar permisos y dispositivo de audio
- **Vosk no carga**: Confirmar ruta del modelo
- **API no responde**: Verificar conexión y API keys
- **Audio no reproduce**: Instalar mpg123 (Linux) o verificar sistema de audio

### Logs y Depuración
La aplicación muestra mensajes en consola para:
- Estado de reconocimiento de voz
- Errores de API
- Estado de micrófono
- Procesamiento de audio

## Licencia y Créditos
- Vosk: Reconocimiento de voz open source
- Edge TTS: Microsoft Azure Speech Services
- Flet: Framework para interfaces Python
- APIs externas: Configurables según preferencia

## Contacto y Soporte
Para reportar problemas o solicitar características, revisar los logs de la aplicación y verificar configuración de dependencias.