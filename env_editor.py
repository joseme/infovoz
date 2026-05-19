import flet as ft
import os

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")


def load_env():
    vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    vars[key.strip()] = value.strip()
    return vars


def save_env(vars):
    with open(ENV_FILE, "w") as f:
        f.write("# Variables de configuracion\n\n")
        for key, value in vars.items():
            f.write(f"{key}={value}\n")


def main(page: ft.Page):
    page.title = "Editor .env"
    page.window.width = 600
    page.window.height = 700
    page.theme = ft.Theme(color_scheme_seed="blue")

    env_vars = load_env()
    fields = {}

    def build_row(key, value, category):
        field = ft.TextField(
            label=key,
            value=value,
            expand=True,
            on_change=lambda e, k=key: update_var(k, e.control.value),
        )
        fields[key] = field
        return ft.Container(
            content=ft.Row([field], spacing=10),
            padding=5,
        )

    categories = {
        "Modelo": ["VOSK_MODEL_PATH"],
        "API Keys": ["infohub_API_KEY", "infohub_URL", "GOOGLE_API_KEY"],
        "Voces TTS": ["VOICE_CAMILO", "VOICE_LUNA", "VOICE_GAEL", "VOICE_DEFAULT"],
        "Audio": ["AUDIO_SAMPLE_RATE", "AUDIO_BLOCK_SIZE", "TTS_SPEED"],
        "Timeouts": ["infohub_TIMEOUT", "GEMINI_TIMEOUT", "MAX_TOKENS"],
        "App": ["APP_PORT", "APP_WIDTH", "APP_HEIGHT", "LOGIN_WIDTH", "LOGIN_HEIGHT"],
        "UI": ["MAX_CHAT_MESSAGES", "UI_UPDATE_INTERVAL", "PROCESSING_INTERVAL"],
        "Workspaces": ["WORKSPACE_1", "WORKSPACE_2", "WORKSPACE_3"],
    }

    def update_var(key, value):
        env_vars[key] = value

    def save_click(e):
        save_env(env_vars)
        page.snack_bar = ft.SnackBar(ft.Text("Guardado correctamente"))
        page.snack_bar.open = True
        page.update()

    content = ft.ListView(expand=True, spacing=10, padding=20)

    for category, keys in categories.items():
        content.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            category,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_700,
                        ),
                        *[
                            build_row(k, env_vars.get(k, ""), category)
                            for k in keys
                            if k in env_vars
                        ],
                    ],
                    spacing=5,
                ),
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=10,
            )
        )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Editor de Configuracion",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                            ft.ElevatedButton(
                                "Guardar", icon=ft.Icons.SAVE, on_click=save_click
                            ),
                        ]
                    ),
                    ft.Divider(),
                    content,
                ],
                spacing=10,
            ),
            expand=True,
            padding=10,
        )
    )


ft.app(main)
