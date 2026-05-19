import os
import sounddevice as sd
import queue
import vosk
import sys
import json
import threading
import flet as ft
import time
import requests
import edge_tts
import asyncio
import subprocess
import platform
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
infohub_API_KEY = os.getenv("infohub_API_KEY")
infohub_URL = os.getenv("infohub_URL", "https://any.knowhub.tech")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

VOZ_CAMILO = os.getenv("VOICE_CAMILO", "es-CO-GonzaloNeural")
VOZ_LUNA = os.getenv("VOICE_LUNA", "es-ES-ElviraNeural")
VOZ_GAEL = os.getenv("VOICE_GAEL", "es-MX-JorgeNeural")
VOZ_DEFAULT = os.getenv("VOICE_DEFAULT", "es-AR-ElenaNeural")

AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_BLOCK_SIZE = int(os.getenv("AUDIO_BLOCK_SIZE", "8000"))
TTS_SPEED = float(os.getenv("TTS_SPEED", "0.85"))

infohub_TIMEOUT = int(os.getenv("infohub_TIMEOUT", "30"))
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "10"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "20"))

APP_PORT = int(os.getenv("APP_PORT", "8550"))
APP_WIDTH = int(os.getenv("APP_WIDTH", "420"))
APP_HEIGHT = int(os.getenv("APP_HEIGHT", "700"))
LOGIN_WIDTH = int(os.getenv("LOGIN_WIDTH", "350"))
LOGIN_HEIGHT = int(os.getenv("LOGIN_HEIGHT", "400"))

MAX_CHAT_MESSAGES = int(os.getenv("MAX_CHAT_MESSAGES", "30"))

infohub_WORKSPACES = {
    1: os.getenv("WORKSPACE_1", "odoo"),
    2: os.getenv("WORKSPACE_2", "blawd"),
    3: os.getenv("WORKSPACE_3", "legal"),
}
UI_UPDATE_INTERVAL = float(os.getenv("UI_UPDATE_INTERVAL", "0.1"))
PROCESSING_INTERVAL = float(os.getenv("PROCESSING_INTERVAL", "0.3"))

# Queue para actualizaciones de UI seguras
ui_queue: queue.Queue = queue.Queue()

# --- CONFIGURACIÓN DE VOSK ---
try:
    model = vosk.Model(VOSK_MODEL_PATH)
except Exception as e:
    print(f"Error cargando el modelo: {e}")
    sys.exit(1)

q: queue.Queue = queue.Queue()

# --- ESTADO GLOBAL ---
transcripcion_activa: bool = False
palabra_clave_activa: Optional[str] = None
page: Optional[ft.Page] = None
audio_proceso: Optional[subprocess.Popen] = None
audio_timers: List[threading.Timer] = []
microfono_habilitado: bool = True
voz_habilitada: bool = True

# --- AUTENTICACIÓN ---
USUARIOS_VALIDOS = {"admin": "admin123", "usuario": "123456"}

# --- CONFIGURACIÓN DE APIS ---


def cargar_usuarios():
    """Carga usuarios desde archivo JSON"""
    try:
        ruta_usuarios = os.path.join(os.path.dirname(__file__), "users.json")
        with open(ruta_usuarios, "r", encoding="utf-8") as f:
            datos = json.load(f)
            return {user["usuario"]: user for user in datos["usuarios"]}
    except Exception as e:
        print(f"Error cargando usuarios: {e}")
        return {}


def guardar_usuarios(usuarios_dict):
    """Guarda usuarios en archivo JSON"""
    try:
        ruta_usuarios = os.path.join(os.path.dirname(__file__), "users.json")
        datos = {"usuarios": list(usuarios_dict.values())}
        with open(ruta_usuarios, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando usuarios: {e}")
        return False


USUARIOS_VALIDOS = cargar_usuarios()

# --- CONFIGURACIÓN TTS MEJORADA ---
VOCES_ASISTENTES = {
    "camilo": VOZ_CAMILO,
    "luna": VOZ_LUNA,
    "gael": VOZ_GAEL,
}

# Thread pools optimizados
api_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="api_")
tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts_")


# --- FUNCIONES DE AUDIO ---
def callback(indata, frames, time_info, status):
    """Callback optimizado de audio"""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


def detener_audio():
    """Detiene la reproducción de audio actual"""
    global audio_proceso, audio_timers
    if audio_proceso:
        try:
            audio_proceso.terminate()
            audio_proceso.kill()
            audio_proceso = None
        except Exception:
            pass
    for timer in audio_timers:
        try:
            timer.cancel()
        except Exception:
            pass
    audio_timers = []


# --- FUNCIONES TTS MEJORADAS ---
def reproducir_audio_mp3_con_callback(audio_bytes, callback_fin=None, velocidad=0.85):
    """Reproduce bytes de audio MP3 con velocidad ajustada y ejecuta callback al terminar"""
    global audio_proceso
    try:
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            temp_file = f.name

        # Crear archivo temporal para audio modificado
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_slow_file = f.name

        def _reproducir_y_terminar():
            global audio_proceso
            audio_proceso = None

            # Ralentizar el audio usando ffmpeg si está disponible
            try:
                # Intentar usar ffmpeg para cambiar la velocidad
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        temp_file,
                        "-filter:a",
                        f"atempo={velocidad}",
                        "-c:a",
                        "libmp3lame",
                        "-q:a",
                        "2",
                        temp_slow_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    archivo_reproducir = temp_slow_file
                else:
                    # Si ffmpeg falla, usar archivo original
                    archivo_reproducir = temp_file

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Si ffmpeg no está disponible, usar archivo original
                archivo_reproducir = temp_file

            # Reproducir el audio
            if platform.system() == "Linux":
                try:
                    audio_proceso = subprocess.Popen(
                        ["mpg123", "-q", archivo_reproducir],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    audio_proceso.wait()
                except FileNotFoundError:
                    print(
                        "⚠️ mpg123 no encontrado. Instálalo con: sudo apt install mpg123"
                    )
                except Exception as e:
                    print(f"⚠️ Error mpg123: {e}")
            elif platform.system() == "Windows":
                import winsound

                winsound.PlaySound(archivo_reproducir, winsound.SND_FILENAME)
            else:
                audio_proceso = subprocess.Popen(
                    ["afplay", archivo_reproducir], capture_output=True
                )
                audio_proceso.wait()

            # Limpiar archivos temporales
            try:
                os.unlink(temp_file)
                if archivo_reproducir != temp_file:
                    os.unlink(temp_slow_file)
            except Exception:
                pass

            audio_proceso = None
            if callback_fin:
                callback_fin()

        threading.Thread(target=_reproducir_y_terminar, daemon=True).start()

    except Exception as e:
        print(f"⚠️ Error reproducción MP3: {e}")
        audio_proceso = None
        if callback_fin:
            callback_fin()


def limpiar_texto_pronunciacion(texto):
    texto = re.sub(r"[^\w\s.,?!;:áéíóúüñÁÉÍÓÚÜÑ¿¡]", "", texto)
    texto = " ".join(texto.split())
    return texto


def texto_a_voz_progresivo(texto, asistente=None, on_char=None, on_fin=None):
    """
    TTS con texto progresivo sincronizado con audio
    - on_char: callback por cada carácter revelado
    - on_fin: callback cuando termina la reproducción
    """
    texto = limpiar_texto_pronunciacion(texto)
    texto_limpio = texto

    def _ejecutar_tts():
        try:
            if asistente and asistente in VOCES_ASISTENTES:
                voz = VOCES_ASISTENTES[asistente]
            else:
                voz = VOZ_DEFAULT

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(
                sintetizar_voz_asincrono(texto_limpio, voz)
            )
            loop.close()

            if audio_bytes:
                char_count = [0]
                timer_ref = [None]

                # Calcular tiempo entre caracteres para sincronizar con audio más lento
                # Ajustar según la longitud del texto y velocidad deseada
                tiempo_base = 0.06  # Tiempo base por carácter (más lento que antes)

                # Para textos más largos, hacer el display un poco más rápido
                if len(texto) > 100:
                    tiempo_base = 0.05
                elif len(texto) > 50:
                    tiempo_base = 0.055

                def mostrar_siguiente():
                    char_count[0] += 1
                    if char_count[0] < len(texto) and on_char:
                        on_char(texto[: char_count[0]])
                        timer_ref[0] = threading.Timer(tiempo_base, mostrar_siguiente)
                        audio_timers.append(timer_ref[0])
                        timer_ref[0].start()
                    elif on_fin:
                        on_fin(texto)

                timer_ref[0] = threading.Timer(tiempo_base, mostrar_siguiente)
                audio_timers.append(timer_ref[0])
                timer_ref[0].start()

                # Reproducir audio con velocidad reducida (85% del original)
                reproducir_audio_mp3_con_callback(
                    audio_bytes, on_fin, velocidad=TTS_SPEED
                )

        except Exception as e:
            print(f"❌ Error en TTS: {e}")
            if on_fin:
                on_fin(texto)

    tts_executor.submit(_ejecutar_tts)


async def sintetizar_voz_asincrono(texto, voz_id):
    """Sintetiza voz usando Edge TTS (MP3) de forma asíncrona"""
    try:
        if len(texto) > 800:
            texto = texto[:797] + "..."

        communicate = edge_tts.Communicate(texto, voz_id)

        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        return b"".join(audio_chunks) if audio_chunks else None

    except Exception as e:
        print(f"❌ Error síntesis voz: {e}")
        return None


def texto_a_voz_natural(texto, asistente=None, sync=False):
    """
    Nueva función TTS con voces naturales
    - No bloquea la interfaz
    - Usa voces específicas por asistente
    - Si sync=True, espera a que termine la reproducción
    """
    texto = limpiar_texto_pronunciacion(texto)
    texto_limpio = texto

    def _ejecutar_tts():
        try:
            # Seleccionar voz
            if asistente and asistente in VOCES_ASISTENTES:
                voz = VOCES_ASISTENTES[asistente]
            else:
                voz = VOZ_DEFAULT

            # Sintetizar
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(
                sintetizar_voz_asincrono(texto_limpio, voz)
            )
            loop.close()

            if audio_bytes:
                reproducir_audio_mp3_con_callback(audio_bytes)
                return True

        except Exception as e:
            print(f"❌ Error en TTS: {e}")

        return False

    if sync:
        return _ejecutar_tts()
    else:
        # Ejecutar en segundo plano sin bloquear
        tts_executor.submit(_ejecutar_tts)
        return None


# --- FUNCIONES DE API OPTIMIZADAS ---
def llamar_api_infohub_async(texto_usuario, ws):
    """Versión optimizada para threads"""
    if not infohub_API_KEY:
        return "API Key no configurada."

    workspace_id = infohub_WORKSPACES.get(ws, "odoo")
    headers = {
        "Authorization": f"Bearer {infohub_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {"message": texto_usuario, "mode": "chat", "max_tokens": MAX_TOKENS}

    try:
        response = requests.post(
            f"{infohub_URL}/api/v1/workspace/{workspace_id}/chat",
            headers=headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        answer = json.loads(response.content)
        textosin = answer["textResponse"]
        characters = "*"
        for x in range(len(characters)):
            textosin = textosin.replace(characters[x], "")
        return textosin
    except requests.exceptions.ConnectionError:
        return "❌ Servidor infohubLLM no disponible. Verifica que esté corriendo en localhost:3051"
    except requests.exceptions.Timeout:
        return "⌛ Timeout - El servidor no responde. Intenta de nuevo"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}"


def llamar_api_gemini_async(texto_usuario):
    """Versión optimizada para threads"""
    if not GOOGLE_API_KEY:
        return "API Key de Google no configurada."

    url = f"https://generativelanguage.googleapis.com/?key={GOOGLE_API_KEY}"
    data = {"contents": [{"parts": [{"text": texto_usuario}]}]}

    try:
        response = requests.post(url, json=data, timeout=GEMINI_TIMEOUT)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.Timeout:
        return "⌛ Timeout - Intenta de nuevo"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:80]}"


def generar_respuesta_ia_thread(texto_usuario, api_nombre):
    """Llama a la API en thread pool"""
    if api_nombre == "camilo":
        return llamar_api_infohub_async(texto_usuario, 1)
    elif api_nombre == "luna":
        return llamar_api_infohub_async(texto_usuario, 2)
    elif api_nombre == "gael":
        return llamar_api_infohub_async(texto_usuario, 3)
    else:
        return "API desconocida."


# --- INTERFAZ FLET OPTIMIZADA ---
def add_message(text, is_user=True, assistant=None, play_audio=True):
    """Agrega mensaje al chat con diseño mejorado"""
    if not page:
        return

    prompt_font = "Roboto"

    if is_user:
        avatar = ft.Container(
            content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=16),
            bgcolor=ft.Colors.BLUE,
            width=32,
            height=32,
            border_radius=16,
            alignment=ft.alignment.Alignment(0, 0),
        )

        text_control = ft.Text(
            text, color=ft.Colors.WHITE, size=14, font_family=prompt_font
        )

        bubble = ft.Container(
            content=text_control,
            bgcolor=ft.Colors.BLUE,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

        row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        bubble,
                        ft.Text(
                            "Tú",
                            size=10,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.RIGHT,
                            expand=True,
                        ),
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.END,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                avatar,
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=8,
        )

        if page and hasattr(page, "chat_column"):
            page.chat_column.controls.append(row)
            if len(page.chat_column.controls) > MAX_CHAT_MESSAGES:
                page.chat_column.controls.pop(0)
            page.chat_column.scroll_to(
                offset=-1, duration=300, curve=ft.AnimationCurve.EASE_OUT
            )
            try:
                page.update()
            except Exception:
                pass
        return

    # Assistant Message
    if assistant == "camilo":
        color = ft.Colors.GREEN
        bg_color = ft.Colors.GREEN_50
        icon = ft.Icons.PERSON
        text_color = ft.Colors.BLACK
    elif assistant == "luna":
        color = ft.Colors.PURPLE
        bg_color = ft.Colors.PURPLE_50
        icon = ft.Icons.FACE
        text_color = ft.Colors.BLACK
    elif assistant == "gael":
        color = ft.Colors.CYAN
        bg_color = ft.Colors.CYAN_50
        icon = ft.Icons.PUBLIC
        text_color = ft.Colors.BLACK
    else:
        color = ft.Colors.GREY
        bg_color = ft.Colors.GREY_50
        icon = ft.Icons.SMART_TOY
        text_color = ft.Colors.BLACK

    avatar = ft.Container(
        content=ft.Icon(icon, color=ft.Colors.WHITE, size=16),
        bgcolor=color,
        width=32,
        height=32,
        border_radius=16,
        alignment=ft.alignment.Alignment(0, 0),
    )

    text_control = ft.Text(
        text, color=text_color, size=14, font_family=prompt_font, selectable=True
    )

    # Si voz habilitada y es mensaje de asistente con audio, iniciar con texto vacío
    if not is_user and play_audio and voz_habilitada:
        text_control.value = ""

    bubble = ft.Container(
        content=text_control,
        bgcolor=bg_color,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=2,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 1),
        ),
        width=max(200, page.width * 0.7) if page else 280,
    )

    row = ft.Row(
        controls=[
            avatar,
            ft.Column(
                controls=[
                    bubble,
                    ft.Text(assistant.capitalize(), size=10, color=ft.Colors.GREY_500),
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.START,
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=8,
    )

    def actualizar_texto(texto_parcial):
        text_control.value = texto_parcial
        try:
            page.update()
        except Exception:
            pass

    def texto_completo(texto_final):
        text_control.value = texto_final
        try:
            page.update()
        except Exception:
            pass
        global microfono_habilitado
        microfono_habilitado = True
        actualizar_indicador_microfono(True)
        print("✅ Micrófono reactivado")

    if page and hasattr(page, "chat_column"):
        page.chat_column.controls.append(row)
        if len(page.chat_column.controls) > MAX_CHAT_MESSAGES:
            page.chat_column.controls.pop(0)
        page.chat_column.scroll_to(
            offset=-1, duration=300, curve=ft.AnimationCurve.EASE_OUT
        )
        try:
            page.update()
        except Exception:
            pass

        if play_audio and assistant and voz_habilitada:
            global microfono_habilitado
            microfono_habilitado = False
            print("🔇 Micrófono desactivado - Procesando...")
            actualizar_indicador_microfono(False)

            # Inicializar con texto vacío
            text_control.value = ""
            page.update()

            texto_a_voz_progresivo(
                text, assistant, on_char=actualizar_texto, on_fin=texto_completo
            )


def actualizar_estado(indicador, color):
    """Actualiza el indicador de estado"""
    if not page:
        return

    def update_status():
        if hasattr(page, "status_content"):
            page.status_content.value = indicador
            page.status_content.color = color
            page.status_container.bgcolor = ft.Colors.with_opacity(0.15, color)
            page.update()

    ui_queue.put(update_status)


def actualizar_indicador_microfono(habilitado):
    """Actualiza el indicador visual del micrófono con animaciones"""
    if not page:
        return

    def update_mic():
        if hasattr(page, "mic_icon_container"):
            if habilitado:
                # Indicador activo
                page.mic_icon.icon = ft.Icons.MIC
                page.mic_icon.color = ft.Colors.WHITE
                page.mic_icon_container.bgcolor = ft.Colors.GREEN
                page.mic_icon_container.shadow = ft.BoxShadow(
                    blur_radius=15,
                    spread_radius=2,
                    color=ft.Colors.with_opacity(0.4, ft.Colors.GREEN),
                )
                page.mic_icon_container.scale = 1.1

                page.mic_text.value = "Escuchando..."
                page.mic_text.color = ft.Colors.GREEN
                page.mic_text.weight = ft.FontWeight.BOLD
            else:
                # Indicador pausado
                page.mic_icon.icon = ft.Icons.MIC_OFF
                page.mic_icon.color = ft.Colors.WHITE
                page.mic_icon_container.bgcolor = ft.Colors.RED
                page.mic_icon_container.shadow = None
                page.mic_icon_container.scale = 1.0

                page.mic_text.value = "Procesando..."
                page.mic_text.color = ft.Colors.RED
                page.mic_text.weight = ft.FontWeight.NORMAL

            page.update()

    ui_queue.put(update_mic)


# --- PROCESAMIENTO DE VOZ OPTIMIZADO ---
def procesar_respuesta_asincrona(texto_usuario, keyword):
    """Procesa respuesta en segundo plano"""
    try:
        # Obtener respuesta
        respuesta = generar_respuesta_ia_thread(texto_usuario, keyword)

        # Actualizar UI con respuesta
        add_message(respuesta, is_user=False, assistant=keyword)

        # Resetear estado
        global transcripcion_activa, palabra_clave_activa
        transcripcion_activa = False
        palabra_clave_activa = None

        # Actualizar estado
        actualizar_estado("💤 Esperando palabra clave...", ft.Colors.GREY)

    except Exception as e:
        print(f"❌ Error procesando respuesta: {e}")
        add_message(f"Error: {str(e)[:100]}", is_user=False, assistant=keyword)


def bucle_reconocimiento():
    """Hilo principal de reconocimiento de voz"""
    global transcripcion_activa, palabra_clave_activa, microfono_habilitado

    rec = vosk.KaldiRecognizer(model, 16000)  # 16kHz para mejor eficiencia
    print("✅ Reconocimiento de voz iniciado")

    buffer_texto = ""
    ultimo_procesamiento = time.time()

    while True:
        try:
            # Obtener datos de audio
            data = q.get(timeout=0.1)

            # Si el micrófono está deshabilitado, no procesar
            if not microfono_habilitado:
                continue

            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                text_lower = text.lower().strip()

                if text_lower:
                    buffer_texto += " " + text_lower

                # Procesar cada 300ms máximo
                tiempo_actual = time.time()
                if tiempo_actual - ultimo_procesamiento < PROCESSING_INTERVAL:
                    continue

                ultimo_procesamiento = tiempo_actual

                # Detectar palabra de parada "alto"
                if "alto" in buffer_texto:
                    detener_audio()
                    buffer_texto = buffer_texto.replace("alto", "").strip()
                    continue

                # Detectar palabras clave
                keywords = ["camilo", "luna", "gael"]
                for keyword in keywords:
                    if keyword in buffer_texto:
                        transcripcion_activa = True
                        palabra_clave_activa = keyword

                        # Asegurar que el micrófono esté habilitado
                        microfono_habilitado = True
                        actualizar_indicador_microfono(True)

                        # Colores por asistente
                        colores = {
                            "camilo": ft.Colors.GREEN,
                            "luna": ft.Colors.PURPLE,
                            "gael": ft.Colors.BLUE,
                        }

                        actualizar_estado(
                            f"🎙️ Escuchando ({keyword.capitalize()})...",
                            colores.get(keyword, ft.Colors.BLUE),
                        )

                        add_message(
                            f"✅ {keyword.capitalize()} activado. ¡Habla ahora!",
                            is_user=False,
                            assistant=keyword,
                            play_audio=False,
                        )

                        buffer_texto = buffer_texto.replace(keyword, "").strip()
                        break

                    # Procesar comando si está activo
                    elif transcripcion_activa and buffer_texto.strip():
                        if len(buffer_texto.strip()) > 1:
                            texto_usuario = buffer_texto.strip()

                            # Mostrar mensaje del usuario
                            add_message(texto_usuario, is_user=True)

                            # Deshabilitar micrófono mientras se procesa y responde
                            microfono_habilitado = False
                            print("🔇 Micrófono desactivado - Procesando...")
                            actualizar_indicador_microfono(False)

                            # Procesar respuesta en thread
                            threading.Thread(
                                target=procesar_respuesta_asincrona,
                                args=(texto_usuario, palabra_clave_activa),
                                daemon=True,
                            ).start()

                        buffer_texto = ""
                else:
                    buffer_texto = ""

        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Error en reconocimiento: {e}")
            buffer_texto = ""


# --- FUNCIONES DE AUTENTICACIÓN ---
def validar_usuario(usuario: str, password: str) -> bool:
    """Valida credenciales de usuario"""
    user_data = USUARIOS_VALIDOS.get(usuario)
    return user_data and user_data["password"] == password


def obtener_datos_usuario(usuario: str) -> dict:
    """Obtiene datos completos del usuario"""
    return USUARIOS_VALIDOS.get(usuario, {})


def agregar_usuario(
    usuario: str, password: str, nombre: str = "", rol: str = "user"
) -> bool:
    """Agrega un nuevo usuario al sistema"""
    global USUARIOS_VALIDOS

    if usuario in USUARIOS_VALIDOS:
        return False  # Usuario ya existe

    nuevo_usuario = {
        "usuario": usuario,
        "password": password,
        "nombre": nombre or usuario,
        "rol": rol,
    }

    USUARIOS_VALIDOS[usuario] = nuevo_usuario
    return guardar_usuarios(USUARIOS_VALIDOS)


def login(p: ft.Page):
    """Pantalla de login"""
    p.title = "InfoVoz AI - Login"
    p.window.width = LOGIN_WIDTH
    p.window.height = LOGIN_HEIGHT
    p.window.resizable = False
    p.bgcolor = ft.Colors.WHITE
    p.window_prevent_close = False
    p.on_window_event = on_window_event

    usuario_field = ft.TextField(
        label="Usuario", width=280, autofocus=True, prefix_icon=ft.Icons.PERSON
    )

    password_field = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        width=280,
        prefix_icon=ft.Icons.LOCK,
    )

    error_text = ft.Text("", color=ft.Colors.RED, size=12)

    def login_click(e):
        if validar_usuario(usuario_field.value, password_field.value):
            datos_usuario = obtener_datos_usuario(usuario_field.value)
            print(
                f"✅ Bienvenido/a {datos_usuario.get('nombre', usuario_field.value)} ({datos_usuario.get('rol', 'user')})"
            )
            p.clean()
            p.window.width = APP_WIDTH
            p.window.height = APP_HEIGHT
            main(p)
        else:
            error_text.value = "Usuario o contraseña incorrectos"
            p.update()

    login_form = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.ASSISTANT, size=48, color=ft.Colors.BLUE_700
                            ),
                            ft.Text(
                                "InfoVoz AI",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_700,
                            ),
                            ft.Text(
                                "Inicia sesión para continuar",
                                size=14,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=20,
                ),
                usuario_field,
                password_field,
                error_text,
                ft.ElevatedButton(
                    "Iniciar Sesión",
                    on_click=login_click,
                    width=280,
                    height=45,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                ),
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=30,
        border_radius=20,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
    )

    p.add(
        ft.Container(
            content=login_form,
            padding=20,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.BLUE_50, ft.Colors.PURPLE_50],
            ),
            expand=True,
        )
    )


# --- FUNCIONES DE INTERFAZ ---
def toggle_voice():
    global voz_habilitada
    voz_habilitada = not voz_habilitada
    if voz_habilitada:
        page.voice_button.icon = ft.Icons.VOLUME_UP
        page.voice_button.tooltip = "Desactivar voz"
        page.voice_button.icon_color = ft.Colors.BLUE
    else:
        page.voice_button.icon = ft.Icons.VOLUME_OFF
        page.voice_button.tooltip = "Activar voz"
        page.voice_button.icon_color = ft.Colors.RED
    page.update()


def procesar_pregunta_escrita(e):
    """Procesa pregunta escrita por el usuario"""
    if not hasattr(page, "pregunta_field") or not page.pregunta_field.value:
        return

    pregunta = page.pregunta_field.value.strip()
    if not pregunta:
        return

    # Seleccionar asistente activo (por defecto el primero)
    asistente_seleccionado = (
        getattr(page, "asistente_dropdown", None).value
        if hasattr(page, "asistente_dropdown") and page.asistente_dropdown
        else "camilo"
    )

    # Mostrar pregunta del usuario
    add_message(pregunta, is_user=True)

    # Limpiar campo
    page.pregunta_field.value = ""
    page.update()

    # Deshabilitar micrófono mientras se procesa y responde
    global microfono_habilitado
    microfono_habilitado = False
    print("🔇 Micrófono desactivado - Procesando pregunta escrita...")
    actualizar_indicador_microfono(False)

    # Procesar respuesta en thread
    threading.Thread(
        target=procesar_respuesta_asincrona,
        args=(pregunta, asistente_seleccionado),
        daemon=True,
    ).start()


# --- INTERFAZ PRINCIPAL FLET ---
def main(p: ft.Page):
    global page
    page = p

    page.title = "Asistente de Voz IA"
    page.window.width = APP_WIDTH
    page.window.height = APP_HEIGHT
    page.window.resizable = True
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.WHITE
    page.theme = ft.Theme(color_scheme_seed="blue", font_family="Roboto")

    def on_resize(e):
        if hasattr(page, "chat_container"):
            page.update()
        if hasattr(page, "input_row"):
            page.update()

    page.on_resize = on_resize
    page.window_prevent_close = False
    page.on_window_event = on_window_event

    # --- HEADER ---
    header = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.GRAPHIC_EQ, size=24, color=ft.Colors.WHITE
                            ),
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                            padding=8,
                            border_radius=12,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "InfoVoz AI",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Asistente Inteligente",
                                    size=11,
                                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[ft.Colors.BLUE_700, ft.Colors.PURPLE_600],
        ),
        padding=ft.padding.symmetric(vertical=20),
        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 5),
        ),
    )

    # --- STATUS BAR ---
    page.status_content = ft.Text(
        "👋 Di 'Camilo', 'Luna' o 'Gael' o escribe tu pregunta",
        color=ft.Colors.BLUE_GREY_600,
        size=13,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    page.status_container = ft.Container(
        content=page.status_content,
        bgcolor=ft.Colors.BLUE_50,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        border_radius=20,
        border=ft.border.all(1, ft.Colors.BLUE_100),
        margin=ft.margin.symmetric(vertical=7.5),
    )

    # --- CHAT AREA ---
    page.chat_column = ft.ListView(
        expand=True,
        spacing=12,
        auto_scroll=True,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
    )

    page.chat_container = ft.Container(
        content=page.chat_column,
        expand=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    # --- INFO PANEL (Available Agents) ---
    def agent_badge(name, color, icon):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=18, color=color),
                        bgcolor=ft.Colors.WHITE,
                        padding=8,
                        border_radius=30,
                        border=ft.border.all(1, color),
                        shadow=ft.BoxShadow(
                            blur_radius=2,
                            color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                        ),
                    ),
                    ft.Text(
                        name,
                        size=10,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=5,
        )

    agents_panel = ft.Container(
        content=ft.Row(
            [
                agent_badge("Camilo", ft.Colors.GREEN, ft.Icons.PERSON),
                agent_badge("Luna", ft.Colors.PURPLE, ft.Icons.FACE),
                agent_badge("Gael", ft.Colors.CYAN, ft.Icons.PUBLIC),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        ),
        bgcolor=ft.Colors.GREY_50,
        padding=10,
        border_radius=15,
        margin=ft.margin.symmetric(horizontal=20),
    )

    # --- INPUT AREA ---
    page.asistente_dropdown = ft.Dropdown(
        label="Asistente",
        options=[
            ft.dropdown.Option("camilo", "Camilo"),
            ft.dropdown.Option("luna", "Luna"),
            ft.dropdown.Option("gael", "Gael"),
        ],
        value="camilo",
        expand=1,
        height=45,
        text_size=12,
    )

    page.pregunta_field = ft.TextField(
        label="Escribe tu pregunta...",
        hint_text="¿Qué quieres saber?",
        expand=True,
        height=40,
        text_size=12,
        on_submit=procesar_pregunta_escrita,
    )

    page.enviar_button = ft.IconButton(
        icon=ft.Icons.SEND,
        tooltip="Enviar pregunta",
        icon_color=ft.Colors.BLUE,
        on_click=procesar_pregunta_escrita,
    )

    page.input_row = ft.Row(
        [
            page.asistente_dropdown,
            page.pregunta_field,
            page.enviar_button,
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    input_area = ft.Container(
        content=page.input_row,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_100),
        border_radius=ft.border_radius.only(top_left=15, top_right=15),
    )

    # --- BOTTOM BAR (Mic & Controls) ---
    page.mic_icon = ft.Icon(ft.Icons.MIC, size=28, color=ft.Colors.WHITE)
    page.mic_icon_container = ft.Container(
        content=page.mic_icon,
        width=56,
        height=56,
        bgcolor=ft.Colors.GREEN,
        border_radius=28,
        shadow=ft.BoxShadow(
            blur_radius=10, color=ft.Colors.with_opacity(0.3, ft.Colors.GREEN)
        ),
        animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_OUT_BACK),
        alignment=ft.alignment.Alignment(0, 0),
    )

    page.mic_text = ft.Text(
        "Escuchando...", size=12, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD
    )

    page.voice_button = ft.IconButton(
        icon=ft.Icons.VOLUME_UP,
        tooltip="Desactivar voz",
        icon_color=ft.Colors.BLUE,
        on_click=lambda e: toggle_voice(),
    )

    bottom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        page.mic_icon_container,
                        ft.Column(
                            [
                                ft.Text("Estado", size=10, color=ft.Colors.GREY_500),
                                page.mic_text,
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                page.voice_button,
                ft.IconButton(
                    icon=ft.Icons.DELETE_SWEEP,
                    tooltip="Limpiar chat",
                    icon_color=ft.Colors.RED,
                    on_click=lambda e: (
                        page.chat_column.controls.clear(),
                        page.update(),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_100),
        border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
        shadow=ft.BoxShadow(
            blur_radius=15,
            color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            offset=ft.Offset(0, -5),
        ),
    )

    # --- MAIN LAYOUT ASSEMBLY ---
    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    page.status_container, alignment=ft.alignment.Alignment(0, 0)
                ),
                page.chat_container,
                agents_panel,
                input_area,
                bottom_bar,
            ],
            spacing=0,
            expand=True,
        )
    )

    # Iniciar reconocimiento después de cargar UI
    def iniciar_procesamiento():
        time.sleep(1)  # Esperar a que la UI esté lista
        t = threading.Thread(target=bucle_reconocimiento, daemon=True)
        t.start()
        print("🚀 Sistema listo. Escuchando...")

    # Timer para procesar actualizaciones de UI
    def process_ui_queue():
        try:
            while True:
                func = ui_queue.get_nowait()
                func()
        except queue.Empty:
            pass
        finally:
            # Programar siguiente ejecución cada 100ms
            import asyncio

            asyncio.get_event_loop().call_later(UI_UPDATE_INTERVAL, process_ui_queue)

    # Iniciar el procesamiento de la queue
    import asyncio

    asyncio.get_event_loop().call_later(UI_UPDATE_INTERVAL, process_ui_queue)

    threading.Thread(target=iniciar_procesamiento, daemon=True).start()


stream = None


def cleanup():
    global stream
    print("Limpiando recursos...")
    try:
        detener_audio()
        if stream:
            stream.stop()
            stream.close()
        api_executor.shutdown(wait=False)
        tts_executor.shutdown(wait=False)
    except Exception:
        pass


def on_window_event(e):
    if e.data == "close":
        cleanup()


# --- INICIALIZACIÓN ---
if __name__ == "__main__":
    try:
        stream = sd.RawInputStream(
            samplerate=AUDIO_SAMPLE_RATE,
            blocksize=AUDIO_BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=callback,
        )
        stream.start()
        print("✅ Audio configurado correctamente")

        ft.app(target=login, view=ft.AppView.FLET_APP, port=APP_PORT)

    except Exception as e:
        print(f"❌ Error inicial: {e}")
    finally:
        cleanup()
