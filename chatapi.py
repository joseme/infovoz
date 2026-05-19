import requests
import json

def enviar_mensaje_anythingllm(mensaje, api_key, workspace_slug, base_url="http://192.168.0.148:3051"):
    """
    Envía un mensaje al workspace especificado de AnythingLLM e imprime la respuesta.
    
    :param mensaje: El texto de la pregunta o comando.
    :param api_key: Tu clave de API de AnythingLLM (Settings > API Keys).
    :param workspace_slug: El identificador (slug) del workspace (ej. 'default').
    :param base_url: La URL base donde corre tu instancia de AnythingLLM.
    """
    
    # Construir la URL específica del endpoint de chat
    # El endpoint suele ser /api/v1/workspace/{slug}/chat
    url = f"http://192.168.0.148:3051/api/v1/workspace/blawd/chat"
    
    # Encabezados necesarios
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Cuerpo de la petición (payload)
    payload = {
        "message": mensaje,
        "mode": "chat"  # Puede ser "chat" o "query"
    }
    
    try:
        print(f"Enviando mensaje a AnythingLLM: {mensaje}")
        
        # Realizar la petición POST
        response = requests.post(url, headers=headers, json=payload)
        
        # Verificar si la petición fue exitosa (Código 200)
        if response.status_code == 200:
            data = response.json()
            
            # AnythingLLM devuelve la respuesta en el campo 'textResponse'
            respuesta_texto = data.get("textResponse", "No se recibió texto en la respuesta.")
            
            # Imprimir la respuesta
            print("-" * 50)
            print("Respuesta de AnythingLLM:")
            print(respuesta_texto)
            print("-" * 50)
            
            return respuesta_texto
        else:
            print(f"Error en la petición: {response.status_code}")
            print("Detalle:", response.text)
            return None
            
    except Exception as e:
        print(f"Ocurrió un error al conectar con el servidor: {e}")
        return None

# --- Ejemplo de Uso ---

if __name__ == "__main__":
    # CONFIGURACIÓN
    # 1. Ve a la configuración de AnythingLLM (Data Manager > API Keys) para crear una.
    MI_API_KEY = "RMQX5QA-0FA4DH9-H7SAJK2-VQZMQ5G" 
    
    # 2. El slug es el nombre del workspace en la URL (ej: http://localhost:3001/workspace/default)
    MI_WORKSPACE_SLUG = "default" 
    
    # 3. Ajusta la URL si usas Docker o una IP diferente
    MI_BASE_URL = "http://localhost:3001" 

    # Mensaje a enviar
    pregunta = "Hola, ¿qué puedes contarme sobre tus documentos?"

    # Llamar a la función
    enviar_mensaje_anythingllm(pregunta, MI_API_KEY, MI_WORKSPACE_SLUG, MI_BASE_URL)