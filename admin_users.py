#!/usr/bin/env python3
"""
Script para administrar usuarios de InfoVoz AI
"""

import json
import os
import sys
import getpass

def cargar_usuarios():
    """Carga usuarios desde archivo JSON"""
    try:
        ruta_usuarios = os.path.join(os.path.dirname(__file__), "users.json")
        with open(ruta_usuarios, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            return datos
    except Exception as e:
        print(f"❌ Error cargando usuarios: {e}")
        return None

def guardar_usuarios(datos):
    """Guarda usuarios en archivo JSON"""
    try:
        ruta_usuarios = os.path.join(os.path.dirname(__file__), "users.json")
        with open(ruta_usuarios, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando usuarios: {e}")
        return False

def listar_usuarios(datos):
    """Lista todos los usuarios"""
    print("\n📋 Lista de Usuarios:")
    print("-" * 50)
    for user in datos['usuarios']:
        print(f"👤 {user['usuario']} ({user['nombre']}) - Rol: {user['rol']}")

def agregar_usuario(datos, usuario, password, nombre, rol):
    """Agrega un nuevo usuario"""
    # Verificar si ya existe
    for user in datos['usuarios']:
        if user['usuario'] == usuario:
            print(f"❌ El usuario '{usuario}' ya existe")
            return False
    
    nuevo_usuario = {
        "usuario": usuario,
        "password": password,
        "nombre": nombre,
        "rol": rol
    }
    
    datos['usuarios'].append(nuevo_usuario)
    if guardar_usuarios(datos):
        print(f"✅ Usuario '{usuario}' agregado correctamente")
        return True
    return False

def eliminar_usuario(datos, usuario):
    """Elimina un usuario"""
    usuarios_originales = len(datos['usuarios'])
    datos['usuarios'] = [u for u in datos['usuarios'] if u['usuario'] != usuario]
    
    if len(datos['usuarios']) < usuarios_originales:
        if guardar_usuarios(datos):
            print(f"✅ Usuario '{usuario}' eliminado correctamente")
            return True
    else:
        print(f"❌ Usuario '{usuario}' no encontrado")
    
    return False

def main():
    print("🔧 Administrador de Usuarios - InfoVoz AI")
    print("=" * 40)
    
    datos = cargar_usuarios()
    if not datos:
        return
    
    while True:
        print("\n📋 Opciones:")
        print("1. Listar usuarios")
        print("2. Agregar usuario")
        print("3. Eliminar usuario")
        print("4. Salir")
        
        opcion = input("\nSelecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            listar_usuarios(datos)
        
        elif opcion == "2":
            usuario = input("👤 Nombre de usuario: ").strip()
            if not usuario:
                print("❌ El usuario no puede estar vacío")
                continue
            
            password = getpass.getpass("🔒 Contraseña: ")
            if not password:
                print("❌ La contraseña no puede estar vacía")
                continue
            
            nombre = input("📝 Nombre completo: ").strip() or usuario
            rol = input("🎭 Rol (admin/user): ").strip().lower() or "user"
            
            if rol not in ["admin", "user"]:
                rol = "user"
            
            agregar_usuario(datos, usuario, password, nombre, rol)
        
        elif opcion == "3":
            listar_usuarios(datos)
            usuario = input("\n🗑️ Nombre de usuario a eliminar: ").strip()
            if usuario:
                if usuario == "admin":
                    print("❌ No puedes eliminar al usuario admin")
                    continue
                eliminar_usuario(datos, usuario)
        
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()