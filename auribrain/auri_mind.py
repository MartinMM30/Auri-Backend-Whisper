# ============================================================
# AURI MIND V9 — Modular, Preciso, Extensible (VERSIÓN FINAL)
# ============================================================

from openai import OpenAI
import re

# Motores base
from auribrain.intent_engine import IntentEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import ActionsEngine
from auribrain.memory_orchestrator import MemoryOrchestrator
from auribrain.fact_extractor import extract_facts
from auribrain.emotion_engine import EmotionEngine
from auribrain.voice_emotion_analyzer import VoiceEmotionAnalyzer

# Modos especiales
from auribrain.crisis_engine import CrisisEngine
from auribrain.focus_engine import FocusEngine
from auribrain.sleep_engine import SleepEngine
from auribrain.love_mode_engine import LoveModeEngine
from auribrain.energy_engine import EnergyEngine
from auribrain.slang_mode_engine import SlangModeEngine
from auribrain.journal_engine import JournalEngine
from auribrain.mental_health_engine import MentalHealthEngine
from auribrain.routine_engine import RoutineEngine
from auribrain.weather_advice_engine import WeatherAdviceEngine

# Smart layers
from auribrain.emotion_smartlayer_v3 import EmotionSmartLayerV3
from auribrain.precision_mode_v2 import PrecisionModeV2



# ============================================================
# AURIMIND V9
# ============================================================

class AuriMindV9:

    # --------------------------------------------------------
    # Personalidades base
    # --------------------------------------------------------
    PERSONALITY = {
        "auri_classic":  {"tone": "cálido y profesional", "emoji": "💜", "length": "medio", "voice": "alloy"},
        "soft":          {"tone": "suave y calmado",      "emoji": "🌙", "length": "corto", "voice": "nova"},
        "siri_style":    {"tone": "formal",               "emoji": "",   "length": "corto", "voice": "verse"},
        "anime_soft":    {"tone": "dulce y expresiva",    "emoji": "✨", "length": "medio", "voice": "hikari"},
        "professional":  {"tone": "serio",                "emoji": "",   "length": "medio", "voice": "amber"},
        "friendly":      {"tone": "amigable",             "emoji": "😊", "length": "medio", "voice": "alloy"},
        "custom_love":   {"tone": "afectiva y suave",     "emoji": "💖", "length": "medio", "voice": "myGF_voice"},
    }


    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------
    def __init__(self):
        self.client = OpenAI()

        # Motores base
        self.context = ContextEngine()
        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.personality = PersonalityEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # Acciones y modos
        self.actions = ActionsEngine()
        self.crisis = CrisisEngine()
        self.sleep = SleepEngine()
        self.slang = SlangModeEngine()
        self.energy = EnergyEngine()
        self.focus = FocusEngine()
        self.journal = JournalEngine()
        self.mental = MentalHealthEngine()
        self.routines = RoutineEngine()
        self.weather = WeatherAdviceEngine()
        self.love = LoveModeEngine()

        # Smart layers
        self.smart = EmotionSmartLayerV3()
        self.precise = PrecisionModeV2()

        self.slang_profile = {}
        self.pending_action = None


    # ============================================================
    # Detectores principales
    # ============================================================

    def _is_technical(self, t):
        KEYS = [
            "derivada", "integral", "ecuación", "resolver", "error",
            "debug", "flutter", "python", "dart", "código", "api",
            "computo", "hpc", "cluster", "matriz", "vector", "dx", "x^"
        ]
        return any(k in t for k in KEYS)

    def _is_info_query(self, t):
        KEYS = [
            "cómo se llama", "como se llama",
            "mis mascotas", "mis perros", "mis gatos",
            "mi mamá", "mi papa", "mi papá",
            "nombre de mi", "nombres de mis",
            "quiero saber", "quiero que me digas"
        ]
        return any(k in t for k in KEYS)


    # ============================================================
    # THINK PIPELINE PRINCIPAL
    # ============================================================
    def think(self, user_msg: str, pcm=None):

        # 0. Validación
        if not user_msg.strip():
            return {"final": "No escuché nada, ¿podrías repetirlo?", "voice_id": "alloy"}

        if not self.context.is_ready():
            return {"final": "Dame un momento… estoy cargando tu perfil 💜", "voice_id": "alloy"}

        txt = user_msg.lower()
        ctx = self.context.get_daily_context()
        uid = ctx["user"]["firebase_uid"]

        # 1. Voz → emoción
        voice_emotion = None
        if pcm:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm)
            except:
                pass

        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion
        )

        # 2. Clasificación
        is_tech = self._is_technical(txt)
        is_info = self._is_info_query(txt)
        intent = self.intent.detect(user_msg)

        # --------------------------------------------------------
        # PRIORIDAD 1: Crisis
        # --------------------------------------------------------
        if self.crisis.detect(user_msg, emotion_snapshot):
            msg = self.crisis.respond(ctx["user"]["name"])
            self.memory.add_semantic(uid, f"[crisis] {user_msg}")
            return {"final": msg, "voice_id": "alloy", "intent": "crisis"}

        # --------------------------------------------------------
        # PRIORIDAD 2: Sueño
        # --------------------------------------------------------
        if not is_tech and not is_info:
            if self.sleep.detect(txt, emotion_snapshot["overall"], ctx):
                return {
                    "final": self.sleep.respond(ctx, emotion_snapshot["overall"]),
                    "voice_id": "alloy",
                    "intent": "sleep"
                }

        # --------------------------------------------------------
        # PRIORIDAD 3: Slang automático
        # --------------------------------------------------------
        slang = None
        if not is_info and not is_tech:
            slang = self.slang.detect(txt, self.slang_profile)

        if slang:
            return {
                "final": self.slang.respond(slang, self.slang_profile),
                "voice_id": "alloy",
                "intent": "slang"
            }

        # --------------------------------------------------------
        # PRIORIDAD 4: Info Query sin LLM
        # --------------------------------------------------------
        if is_info:
            answer = self._resolve_info(uid, txt)
            self.memory.add_dialog(uid, "user", user_msg)
            self.memory.add_dialog(uid, "assistant", answer)
            return {"final": answer, "intent": "info", "voice_id": "alloy"}

        # --------------------------------------------------------
        # PRIORIDAD 5: Technical Mode
        # --------------------------------------------------------
        if is_tech or self.precise.detect(user_msg):
            final = self._llm(uid, user_msg, ctx, emotion_snapshot, precise=True)
            return {"final": final, "voice_id": "verse", "intent": intent}

        # --------------------------------------------------------
        # PRIORIDAD 6: Otros modos inteligentes
        # --------------------------------------------------------
        if self.focus.detect(txt):
            return {"final": self.focus.respond(ctx), "voice_id": "alloy", "intent": "focus"}

        if self.energy.detect(txt, emotion_snapshot["energy"]):
            return {"final": self.energy.respond("boost", ctx), "voice_id": "alloy", "intent": "energy"}

        if "clima" in txt or "outfit" in txt or "frio" in txt or "lluvia" in txt:
            if self.weather.detect(ctx):
                return {"final": self.weather.respond("auto"), "voice_id": "alloy", "intent": "weather"}

        if self.mental.detect(txt, emotion_snapshot["stress"]):
            return {"final": self.mental.respond(), "voice_id": "alloy", "intent": "mental"}

        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(uid, entry)

        if "rutina" in txt or "mi día" in txt or "mi dia" in txt:
            if self.routines.detect(ctx, emotion_snapshot):
                return {"final": self.routines.respond("auto"), "voice_id": "alloy", "intent": "routine"}

        # --------------------------------------------------------
        # Auto aprendizaje familiar
        # --------------------------------------------------------
        self._auto_family(uid, txt)

        # --------------------------------------------------------
        # RESPUESTA GENERAL LLM
        # --------------------------------------------------------
        final = self._llm(uid, user_msg, ctx, emotion_snapshot, precise=False)

        # Guardar diálogo
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)

        # Memoria semántica
        if not is_tech and not is_info:
            self.memory.add_semantic(uid, f"user: {user_msg}")
            self.memory.add_semantic(uid, f"assistant: {final}")

        # Hechos estructurados
        try:
            for f in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, f)
        except:
            pass

        return {"final": final, "voice_id": "alloy", "intent": intent}



    # ============================================================
    # INFO QUERY 2.0 (sin LLM)
    # ============================================================

    def _resolve_info(self, uid, txt):

        ROLES = {
            "mamá": "madre", "mama": "madre",
            "papá": "padre", "papa": "padre",
            "hermano": "hermano", "hermana": "hermana",
            "abuelo": "abuelo", "abuela": "abuela",
            "novia": "pareja", "pareja": "pareja",
        }

        # Familia
        for word, role in ROLES.items():
            if word in txt:
                items = self.memory.get_family_by_role(uid, role)
                if items:
                    names = [f.get("name") for f in items if f.get("name")]
                    if len(names) == 1:
                        return f"Tu {role} se llama {names[0]}."
                    elif len(names) > 1:
                        return f"Tus {role}s se llaman: {', '.join(names)}."
                return f"No tengo guardado el nombre de tu {role}. ¿Querés decírmelo?"

        # Mascotas
        if "mascotas" in txt or "animales" in txt:
            pets = self.memory.get_pets(uid)
            if not pets:
                return "Todavía no tengo registradas tus mascotas. ¿Querés decirme sus nombres?"
            names = ", ".join([p.get("name") for p in pets if p.get("name")])
            return f"Tus mascotas son: {names}."

        return "Todavía no tengo ese dato guardado. ¿Querés contármelo?"


    # ============================================================
    # LLM (general o técnico)
    # ============================================================

    def _llm(self, uid, msg, ctx, emotion, precise=False):

        profile = ctx["prefs"].get("personality", "auri_classic")
        sty = self.PERSONALITY.get(profile, self.PERSONALITY["auri_classic"])

        if precise:
            sty = {"tone": "técnico y directo", "emoji": "", "length": "corto", "voice": "verse"}

        system_prompt = f"""
Eres Auri, asistente personal: emocional, preciso y atento.

REGLAS:
1. Nunca inventes datos personales del usuario.
2. Si el usuario está emocional, respondé con calidez.
3. Si es consulta técnica: respondé conciso y directo.
4. Si es conversación normal: respondé natural y amable.
5. Siempre mantené coherencia con la personalidad seleccionada.

Personalidad:
- Tono: {sty['tone']} {sty['emoji']}
- Precisión técnica: {precise}
"""

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg},
            ]
        )

        return (resp.output_text or "").strip()



    # ============================================================
    # Auto-aprendizaje familiar
    # ============================================================

    def _auto_family(self, uid, txt):
        m = re.search(r"mi (\w+)(?:\s+se llama)?\s+([a-záéíóúñ]+)", txt)
        if m:
            role = m.group(1).lower()
            name = m.group(2).capitalize()

            self.memory.add_fact_structured(uid, {
                "type": "family_member",
                "role": role,
                "name": name,
                "text": f"{role.capitalize()}: {name}",
                "category": "relationship",
                "importance": 4,
                "confidence": 0.95,
            })


    # ============================================================
    # UID DESDE WEBSOCKET
    # ============================================================

    def set_user_uid(self, uid: str):
        """
        Asignación UID para server.py y STT.
        Prepara el perfil de memoria para ese usuario.
        """
        if not uid:
            return

        try:
            # ContextEngine Update (debe existir este método)
            if hasattr(self.context, "set_user_uid"):
                self.context.set_user_uid(uid)

            # Precarga de memoria
            self.memory.get_user_profile(uid)
            self.memory.get_recent_dialog(uid)
            self.memory.get_facts(uid)

            print(f"UID detectado por AuriMind: {uid}")

        except Exception as e:
            print(f"[AuriMindV9] Error asignando UID: {e}")



# Compatibilidad retro
AuriMind  = AuriMindV9
AuriMindV6 = AuriMindV9
AuriMindV7 = AuriMindV9
AuriMindV8 = AuriMindV9
