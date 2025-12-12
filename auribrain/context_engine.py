# auribrain/context_engine.py

from datetime import datetime
from typing import Any, Dict, List

VALID_PLANS = {"free", "pro", "ultra"}

# Imports opcionales de Firebase (no rompen si no están instalados)
try:
    import firebase_admin
    from firebase_admin import auth, firestore
except ImportError:
    firebase_admin = None
    auth = None
    firestore = None


class ContextEngine:

    def __init__(self):
        # UID del usuario autenticado (WEBsocket)
        self._active_uid = None

        # USER
        self.user = {
            "name": None,
            "city": None,
            "birthday": None,
            "occupation": None,
            "firebase_uid": None,
            "plan": "free",  # 🔥 PLAN agregado (por defecto FREE)
        }

        # WEATHER
        self.weather = {
            "temp": None,
            "description": None,
            "timestamp": None,
        }

        # AGENDA
        self.events: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.exams: List[Dict[str, Any]] = []
        self.birthdays: List[Dict[str, Any]] = []
        self.payments: List[Dict[str, Any]] = []

        # PREFS
        self.prefs = {
            "shortReplies": False,
            "softVoice": False,
            "personality": "auri_classic",
        }

        # TIMEZONE
        self.tz = "UTC"

        # TIME / DATE
        self.current_time_iso = None
        self.current_time_pretty = None
        self.current_date_pretty = None

        # Ready flag
        self.ready_flag = False

    # ===========================================================
    # 🔐 UID desde WebSocket
    # ===========================================================
    def set_user_uid(self, uid: str):
        """ Guarda UID del usuario y lo mete al bloque user """
        self._active_uid = uid
        self.user["firebase_uid"] = uid
        print(f"[ContextEngine] UID registrado en contexto: {uid}")

    def get_user_uid(self):
        return self._active_uid

    # ===========================================================
    # PLAN — Sistema de Suscripciones
    # ===========================================================
    def set_user_plan(self, plan: str):
        """ Establece el plan actual del usuario """
        plan = (plan or "").lower().strip()
        if plan not in VALID_PLANS:
            plan = "free"
        self.user["plan"] = plan
        print(f"[ContextEngine] Plan establecido: {plan}")

    def get_user_plan(self) -> str:
        """ Devuelve el plan actual del usuario """
        plan = self.user.get("plan", "free")
        if plan not in VALID_PLANS:
            return "free"
        return plan

    def update_user_plan(self, uid: str, new_plan: str):
        """
        Actualiza el plan del usuario.
        Aquí en el futuro se integra con Firestore + Firebase Claims.
        """
        if uid and uid != self._active_uid:
            print("[ContextEngine] Advertencia: intento de actualizar plan de UID no activo")

        plan = (new_plan or "").lower().strip()
        if plan not in VALID_PLANS:
            plan = "free"

        self.user["plan"] = plan
        print(f"[ContextEngine] Plan actualizado en contexto para UID={uid}: {plan}")

    def sync_plan_from_firebase(self):
        """
        Lee el plan desde Firebase Auth (custom claims) y/o Firestore
        y actualiza self.user['plan'] + otros campos del usuario.
        Se llama típicamente justo después de set_user_uid().
        """
        if not firebase_admin or not auth or not firestore:
            print("[ContextEngine] Firebase Admin no inicializado; skip sync_plan_from_firebase")
            return

        uid = self._active_uid
        if not uid:
            print("[ContextEngine] No hay UID activo para sync_plan_from_firebase")
            return

        try:
            # 1) Custom claims (rápido)
            user_record = auth.get_user(uid)
            claims = user_record.custom_claims or {}
            plan = claims.get("plan")

            # 2) Firestore (fuente de verdad más completa)
            db = firestore.client()
            doc_ref = db.collection("users").document(uid)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                # Si Firestore tiene plan, priorizarlo
                if data.get("plan"):
                    plan = data["plan"]

                # De paso sincronizar otros campos si están
                for key in ("name", "city", "birthday", "occupation"):
                    if key in data:
                        self.user[key] = data[key]

            if plan:
                self.set_user_plan(plan)
            else:
                # si nada definió un plan, garantizamos free
                self.set_user_plan("free")

            print(f"[ContextEngine] Sync plan desde Firebase OK: {self.user['plan']}")

        except Exception as e:
            print(f"[ContextEngine] Error en sync_plan_from_firebase: {e}")

    # ===========================================================
    # SETTERS PARA SÍNCRO DE CONTEXTO
    # ===========================================================
    def set_weather(self, w):
        self.weather = {
            "temp": getattr(w, "temp", None),
            "description": getattr(w, "description", None),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def set_user(self, data: Dict[str, Any]):
        for k in ["name", "city", "birthday", "occupation"]:
            if k in data:
                self.user[k] = data[k]

        # No borrar UID si ya lo tenemos
        if "firebase_uid" in data and data["firebase_uid"]:
            self.user["firebase_uid"] = data["firebase_uid"]

        # Si el backend envía plan en el paquete user, lo integramos
        if "plan" in data:
            self.set_user_plan(data["plan"])

    def set_events(self, events):
        self.events = events or []

    def set_classes(self, classes):
        self.classes = classes or []

    def set_exams(self, exams):
        self.exams = exams or []

    def set_birthdays(self, bds):
        self.birthdays = bds or []

    def set_payments(self, payments):
        self.payments = payments or []

    def set_prefs(self, prefs):
        for k in self.prefs.keys():
            if k in prefs:
                self.prefs[k] = prefs[k]

    def set_timezone(self, tz: str):
        self.tz = tz

    def set_time_info(self, iso=None, pretty=None, date=None):
        if iso:
            self.current_time_iso = iso
        if pretty:
            self.current_time_pretty = pretty
        if date:
            self.current_date_pretty = date

    # ===========================================================
    # READY CONTROL
    # ===========================================================
    def is_ready(self) -> bool:
        return self.ready_flag

    def mark_ready(self):
        self.ready_flag = True

    def invalidate(self):
        self.ready_flag = False

    # ===========================================================
    # CONTEXTO FINAL PARA AURIMIND
    # ===========================================================
    def get_daily_context(self):
        return {
            "user": self.user,
            "weather": self.weather,
            "events": self.events,
            "classes": self.classes,
            "exams": self.exams,
            "birthdays": self.birthdays,
            "payments": self.payments,
            "prefs": self.prefs,
            "timezone": self.tz,
            "current_time_iso": self.current_time_iso,
            "current_time_pretty": self.current_time_pretty,
            "current_date_pretty": self.current_date_pretty,
            "ready": self.ready_flag,
        }
