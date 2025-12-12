# auribrain/auri_singleton.py

from auribrain.auri_mind import AuriMind  # V10.6 (alias en tu archivo)
from auribrain.firebase_init import init_firebase

# Inicializar Firebase antes de Auri
init_firebase()

# Instancia global de AuriMind
auri = AuriMind()

print("🔥 AuriMind V10.6 inicializado correctamente")
