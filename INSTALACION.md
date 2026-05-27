# Manual de Instalación — InfoVoz AI

## Requisitos mínimos

- Python 3.8+
- Conexión a internet (para descargar modelo Vosk y dependencias)
- Micrófono funcionando
- 500 MB de espacio libre en disco

---

## 1. Instalación local

### 1.1 Dependencias del sistema

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv portaudio19-dev mpg123 ffmpeg espeak
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip portaudio mpg123 ffmpeg espeak
```

**macOS:**
```bash
brew install portaudio mpg123 ffmpeg espeak
```

**Windows:**
No requiere dependencias adicionales del sistema.

### 1.2 Clonar el repositorio

```bash
git clone https://github.com/joseme/infovoz.git
cd infovoz
```

### 1.3 Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
```

### 1.4 Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.5 Descargar modelo Vosk (español)

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
rm vosk-model-small-es-0.42.zip
```

### 1.6 Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus claves:

```bash
cp .env.example .env
```

Edita `.env`:

```ini
# (Opcional) API key de AnythingLLM
ANYTHING_KEY=tu_api_key_aqui
ANYTHING_URL=https://tu-servidor-anythingllm.com

# (Opcional) API key de Google Gemini
GOOGLE_API_KEY=tu_api_key_aqui
```

> Sin API keys la app funciona pero los asistentes no podrán responder. Puedes obtener una key de Gemini gratis en https://aistudio.google.com/app/apikey

### 1.7 Crear usuarios

El archivo `users.json` se genera automáticamente al iniciar sesión por primera vez. También puedes crearlo manualmente:

```bash
cp users.example.json users.json
```

### 1.8 Ejecutar

```bash
python main.py
```

La app se abre en una ventana nativa. En Linux puede aparecer como `http://localhost:8550` si Flet decide usar el navegador.

---

## 2. Instalación con Docker (recomendado)

Docker encapsula todas las dependencias incluido el modelo Vosk. Solo necesitas Docker y Docker Compose.

### 2.1 Requisitos

- Docker 24+
- Docker Compose 2.20+

### 2.2 Clonar y configurar

```bash
git clone https://github.com/joseme/infovoz.git
cd infovoz
cp .env.example .env
# Edita .env con tus API keys
```

### 2.3 Construir y arrancar

```bash
docker compose up -d
```

La primera vez descargará el modelo Vosk (~50 MB) e instalará todas las dependencias automáticamente. Tarda 2-5 minutos.

### 2.4 Acceder

Abre el navegador en:

```
http://localhost:8550
```

### 2.5 Ver logs

```bash
docker compose logs -f
```

### 2.6 Detener

```bash
docker compose down
```

### 2.7 Actulizar a nueva versión

```bash
git pull
docker compose up -d --build
```

---

## 3. Configuración avanzada

### 3.1 Variables de entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `ANYTHING_KEY` | — | API key de AnythingLLM |
| `ANYTHING_URL` | `https://any.knowhub.tech` | URL del servidor AnythingLLM |
| `GOOGLE_API_KEY` | — | API key de Google Gemini |
| `VOSK_MODEL_PATH` | `./vosk-model-small-es-0.42` | Ruta al modelo Vosk |
| `USERS_FILE` | `./users.json` | Ruta al archivo de usuarios |
| `FLET_WEB` | — | Si se define, usa el navegador en vez de ventana nativa |

### 3.2 Personalizar asistentes

Edita el diccionario `VOCES_ASISTENTES` en `main.py` para cambiar las voces TTS. Las voces disponibles de Edge TTS se listan en `edgevoces.txt`.

### 3.3 Agregar usuarios

Desde la pantalla de login usa el enlace "¿No tienes cuenta?" para registrarte. O edita directamente `users.json`:

```json
{
  "usuarios": [
    {
      "usuario": "admin",
      "password": "admin123",
      "nombre": "Admin"
    }
  ]
}
```

---

## 4. Solución de problemas

### Error "ALSA lib" en Linux
```bash
# Instalar alsa-utils si faltan
sudo apt install alsa-utils
# Agregar usuario al grupo audio
sudo usermod -aG audio $USER
# Cerrar sesión y volver a entrar
```

### El micrófono no funciona en Docker
```bash
# Asegúrate de que el host tenga PulseAudio corriendo
# y de que el usuario esté en el grupo "audio"
groups $USER
# Debería incluir "audio", si no:
sudo usermod -aG audio $USER
```

### Error cargando el modelo Vosk
Verifica que la ruta en `VOSK_MODEL_PATH` apunte al directorio descomprimido del modelo.

### La API de Gemini no responde
Ve a https://aistudio.google.com/app/apikey y verifica que la key esté activa y tenga habilitada la facturación (el uso gratuito tiene cuota).

---

## 5. Estructura del proyecto

```
infovoz/
├── main.py                  # Aplicación principal
├── main2.py                 # Versión alternativa
├── admin_users.py           # Gestión de usuarios
├── env_editor.py            # Editor de variables de entorno
├── msaudio.py               # Utilidades de audio
├── chatapi.py               # Cliente de APIs
├── requirements.txt         # Dependencias Python
├── Dockerfile               # Construcción Docker
├── docker-compose.yml       # Orquestación Docker
├── .env.example             # Ejemplo de variables de entorno
├── users.json               # Usuarios registrados
├── vosk-model-small-es-0.42/# Modelo de reconocimiento de voz
└── README.md                # Documentación principal
```
