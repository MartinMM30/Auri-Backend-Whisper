import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Credenciales desde variable de entorno JSON
FIREBASE_CREDS_RAW = os.getenv("FIREBASE_CREDENTIALS_JSON")

firebase_app = None


def init_firebase():
    global firebase_app

    if firebase_app:
        return firebase_app

    if not FIREBASE_CREDS_RAW:
        print("⚠ No hay FIREBASE_CREDENTIALS_JSON en entorno — Firebase Admin NO iniciado")
        return None

    try:
        # Convertir la cadena JSON a dict
        creds_dict = json.loads(FIREBASE_CREDS_RAW)

        # Crear credenciales desde dict
        cred = credentials.Certificate(creds_dict)

        firebase_app = firebase_admin.initialize_app(cred)
        print("🔥 Firebase Admin inicializado correctamente")
        return firebase_app

    except Exception as e:
        print(f"❌ Error inicializando Firebase Admin: {e}")
        return None
