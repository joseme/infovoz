# Análisis del Proyecto InfoVoz

## Resumen

**InfoVoz** es un asistente de voz con IA desarrollado en Python que permite interacción por voz y texto con múltiples agentes. Utiliza tecnologías de reconocimiento y síntesis de voz para crear una experiencia conversacional.

---

## Arquitectura

| Componente | Tecnología | Descripción |
|------------|------------|--------------|
| **UI** | Flet | Framework Flutter para Python |
| **STT** | Vosk | Reconocimiento de voz offline (modelo español) |
| **TTS** | Edge TTS | Síntesis de voz Microsoft (gratuito) |
| **LLM** | AnythingLLM + Gemini | APIs de modelos de lenguaje |
| **Audio** | sounddevice, mpg123, ffmpeg | Captura y reproducción de audio |

---

## Funcionalidades Principales

### Asistentes Disponibles
- **Camilo** - Color verde, voz es-CO-GonzaloNeural
- **Luna** - Color púrpura, voz es-ES-ElviraNeural
- **Gael** - Color cyan, voz es-MX-JorgeNeural

### Control por Voz
- Activación por palabra clave: "Camilo", "Luna" o "Gael"
- Comando de parada: "alto" para detener audio
- Interrupción: "ok Camilo" para cambiar de agente mientras habla

### Entrada por Texto
- Campo de texto para preguntas escritas
- Selector de asistente (dropdown)
- Botón de envío o Enter para procesar

### Sincronización Audio-Texto
- Audio reproducido al 85% de velocidad original
- Texto mostrado progresivamente sincronizado
- Tiempos adaptativos según longitud del texto

### Autenticación
- Sistema de login con usuarios en `users.json`
- Roles de usuario (admin, user)
- Contraseñas hasheadas

---

## Estructura del Proyecto

```
infovoz/
├── main.py              # Aplicación principal (1306 líneas)
├── main2.py             # Versión alternativa
├── chatapi.py           # Módulo de API de chat
├── msaudio.py           # Módulo de audio
├── admin_users.py       # Gestión de usuarios
├── pyproject.toml       # Configuración del proyecto
├── requirements-*.txt   # Dependencias
├── users.json           # Base de datos de usuarios
└── vosk-model-*/        # Modelos de reconocimiento de voz
```

---

## Dependencias

### Core
```
python>=3.8
```

### Audio
```
vosk==0.3.45
sounddevice==0.4.6
numpy>=1.24.0
```

### Interfaz
```
flet==0.17.0
```

### APIs y Utilidades
```
edge-tts==6.1.9
requests>=2.31.0
psutil>=5.9.0
python-dotenv>=1.0.0
loguru>=0.7.0
```

---

## Flujo de Funcionamiento

1. **Inicio**: Login de usuario → Carga de modelo Vosk → Inicio de stream de audio
2. **Escucha**: Captura continua de audio a 16kHz
3. **Detección**: Reconocimiento de palabras clave (Camilo/Luna/Gael)
4. **Transcripción**: Captura del habla del usuario
5. **Procesamiento**: Llamada a API de IA (AnythingLLM/Gemini)
6. **Respuesta**: Síntesis TTS + reproducción de audio + visualización progresiva

---

## APIs Externas

| API | Uso | Configuración |
|-----|-----|---------------|
| AnythingLLM | Chat con workspaces (odoo, blawd, legal) | API Key en código |
| Gemini | Respuestas de IA | Google API Key |
| Edge TTS | Síntesis de voz | Sin clave (gratuito) |

---

## Consideraciones de Seguridad

### Recomendaciones
- ❌ API keys actualmente hardcodeadas (líneas 49, 53 de main.py)
- ✅ Usar variables de entorno para credenciales sensibles
- ✅ Implementar `.env` con `python-dotenv`

### Ejemplo de mejora
```python
from dotenv import load_dotenv
import os

load_dotenv()
ANYTHING_KEY = os.getenv("ANYTHING_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

---

## Rendimiento

- **Modelo Vosk**: Versión pequeña (small) - balance velocidad/precisión
- **Audio**: 16kHz sampling, blocksize 8000
- **Thread Pools**: 2 workers para API, 1 para TTS
- **Sincronización**: Tiempos adaptativos 0.05-0.06s por carácter

---

## Posibles Mejoras

1. **Seguridad**: Mover credenciales a variables de entorno
2. **Modelos**: Considerar modelo Vosk completo para mayor precisión
3. **Cacheo**: Implementar caché para respuestas frecuentes
4. **Logging**: Centralizar logs con Loguru (ya instalado)
5. **Tests**: Agregar suite de pruebas unitarias
6. **Docker**: Crear Dockerfile para despliegue

---

## Comandos de Ejecución

```bash
# Instalación
pip install -r requirements-minimal.txt

# Ejecución
python main.py

# Con desarrollo
pip install -r requirements-dev.txt
```

---

*Documento generado: Marzo 2026*
