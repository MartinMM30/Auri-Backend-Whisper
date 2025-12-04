# ============================================================
# AURI MIND V9.1 — Modular, Preciso, Extensible
# ============================================================

from openai import OpenAI
import re

# Motores base
from auribrain.intent_engine import IntentEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import ActionsEngine
from auribrain.entity_extractor import EntityExtractor
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
# AURIMIND V9.1
# ============================================================

class AuriMindV9:

    # --------------------------------------------------------
    # Personalidades base
    # --------------------------------------------------------
    PERSONALITY = {
        "auri_classic": {
            "tone": "cálido y profesional",
            "emoji": "💜",
            "length": "medio",
            "voice": "alloy",
        },
        "soft": {
            "tone": "suave y calmado",
            "emoji": "🌙",
            "length": "corto",
            "voice": "nova",
        },
        "siri_style": {
            "tone": "formal",
            "emoji": "",
            "length": "corto",
            "voice": "verse",
        },
        "anime_soft": {
            "tone": "dulce y expresiva",
            "emoji": "✨",
            "length": "medio",
            "voice": "hikari",
        },
        "professional": {
            "tone": "serio",
            "emoji": "",
            "length": "medio",
            "voice": "amber",
        },
        "friendly": {
            "tone": "amigable",
            "emoji": "😊",
            "length": "medio",
            "voice": "alloy",
        },
        "custom_love": {
            "tone": "afectiva y suave",
            "emoji": "💖",
            "length": "medio",
            "voice": "myGF_voice",
        },
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

        # Acciones
        self.actions = ActionsEngine()

        # Modos
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

    def _is_technical(self, t: str) -> bool:
        KEYS = [
            "derivada", "integral", "ecuación", "ecuacion", "resolver",
            "límite", "limite", "matriz", "vector", "polinomio",
            "debug", "error", "stacktrace", "flutter", "python", "dart",
            "código", "codigo", "api", "endpoint", "backend", "frontend",
            "computo", "cómputo", "hpc", "cluster", "x^", "dx",
        ]
        return any(k in t for k in KEYS)

    def _is_info_query(self, t: str) -> bool:
        KEYS = [
            "cómo se llama", "como se llama",
            "cómo se llaman", "como se llaman",
            "mis mascotas", "mis perros", "mis gatos", "mis animales",
            "mis padres", "mi mamá", "mi mama", "mi papá", "mi papa",
            "nombre de mi", "nombres de mis",
            "quiero saber el nombre",
            "dime el nombre de",
            "quiero que me digas",
        ]
        return any(k in t for k in KEYS)

    # ============================================================
    # THINK PIPELINE PRINCIPAL
    # ============================================================

    def think(self, user_msg: str, pcm=None):
        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {
                "final": "No escuché nada, ¿podrías repetirlo?",
                "voice_id": "alloy",
                "intent": "unknown",
                "action": None,
            }

        if not self.context.is_ready():
            return {
                "final": "Dame un momento… estoy cargando tu perfil 💜",
                "voice_id": "alloy",
                "intent": "wait",
                "action": None,
            }

        txt = user_msg.lower()
        ctx = self.context.get_daily_context()
        uid = (ctx.get("user") or {}).get("firebase_uid")

        if not uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "voice_id": "alloy",
                "intent": "auth_required",
                "action": None,
            }

        # --------------------------------------------------------
        # Personalidad / voz base
        # --------------------------------------------------------
        prefs = ctx.get("prefs") or {}
        profile_key = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY.get(profile_key, self.PERSONALITY["auri_classic"])
        base_voice = style["voice"]

        # --------------------------------------------------------
        # VOZ → emoción
        # --------------------------------------------------------
        voice_emotion = None
        if pcm:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm)
            except Exception:
                pass

        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall = emotion_snapshot.get("overall")
        stress = float(emotion_snapshot.get("stress", 0.2))
        energy_level = float(emotion_snapshot.get("energy", 0.5))

        # Si está muy mal, deshabilitamos humor
        no_humor = stress > 0.4 or overall in ["sad", "angry", "anxious", "overwhelmed"]

        # --------------------------------------------------------
        # Clasificación
        # --------------------------------------------------------
        is_tech = self._is_technical(txt)
        is_info = self._is_info_query(txt)
        intent = self.intent.detect(user_msg)

        # --------------------------------------------------------
        # 1) Crisis (máxima prioridad)
        # --------------------------------------------------------
        if self.crisis.detect(user_msg, emotion_snapshot):
            msg = self.crisis.respond((ctx.get("user") or {}).get("name"))
            self.memory.add_semantic(uid, f"[crisis] {user_msg}")
            return {
                "final": msg,
                "voice_id": base_voice,
                "intent": "crisis",
                "action": None,
            }

        # --------------------------------------------------------
        # 2) Sleep
        # --------------------------------------------------------
        if not is_tech and not is_info:
            if self.sleep.detect(txt, overall, ctx):
                msg = self.sleep.respond(ctx, overall)
                return {
                    "final": msg,
                    "voice_id": base_voice,
                    "intent": "sleep",
                    "action": None,
                }

        # --------------------------------------------------------
        # 3) Slang
        # --------------------------------------------------------
        slang = None
        if not is_info and not is_tech:
            slang = self.slang.detect(txt, self.slang_profile)

        if slang:
            msg = self.slang.respond(slang, self.slang_profile)
            return {
                "final": msg,
                "voice_id": base_voice,
                "intent": "slang",
                "action": None,
            }

        # --------------------------------------------------------
        # 4) Info Query (resolver sin LLM, nombres/mis datos)
        # --------------------------------------------------------
        if is_info:
            answer = self._resolve_info(uid, txt)
            self.memory.add_dialog(uid, "user", user_msg)
            self.memory.add_dialog(uid, "assistant", answer)
            return {
                "final": answer,
                "intent": "info",
                "voice_id": base_voice,
                "action": None,
            }

        # --------------------------------------------------------
        # 5) Technical Mode (modo precisión ON)
        # --------------------------------------------------------
        precise_flag = is_tech or self.precise.detect(user_msg)
        if precise_flag:
            final = self._llm(
                uid=uid,
                msg=user_msg,
                ctx=ctx,
                emotion=emotion_snapshot,
                precise=True,
                no_humor=no_humor,
            )
            # Voz técnica por defecto
            voice_id = "verse"
            return {
                "final": final,
                "voice_id": voice_id,
                "intent": intent,
                "action": None,
            }

        # --------------------------------------------------------
        # 6) Otros modos inteligentes
        # --------------------------------------------------------
        if self.focus.detect(txt):
            return {
                "final": self.focus.respond(ctx),
                "voice_id": base_voice,
                "intent": "focus",
                "action": None,
            }

        if self.energy.detect(txt, energy_level):
            return {
                "final": self.energy.respond("boost", ctx),
                "voice_id": base_voice,
                "intent": "energy",
                "action": None,
            }

        if any(k in txt for k in ["clima", "tiempo", "outfit", "frio", "frío", "lluvia"]):
            if self.weather.detect(ctx):
                return {
                    "final": self.weather.respond("auto"),
                    "voice_id": base_voice,
                    "intent": "weather",
                    "action": None,
                }

        if self.mental.detect(txt, stress):
            return {
                "final": self.mental.respond(),
                "voice_id": base_voice,
                "intent": "mental",
                "action": None,
            }

        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(uid, entry)

        if any(k in txt for k in ["rutina", "mi día", "mi dia", "organizar mi día", "organizar mi dia"]):
            if self.routines.detect(ctx, emotion_snapshot):
                return {
                    "final": self.routines.respond("auto"),
                    "voice_id": base_voice,
                    "intent": "routine",
                    "action": None,
                }

        # --------------------------------------------------------
        # 7) Autoaprendizaje familiar / datos simples
        # --------------------------------------------------------
        self._auto_family(uid, txt)

        # --------------------------------------------------------
        # 8) LLM GENERAL
        # --------------------------------------------------------
        final = self._llm(
            uid=uid,
            msg=user_msg,
            ctx=ctx,
            emotion=emotion_snapshot,
            precise=False,
            no_humor=no_humor,
        )

        # Acciones (recordatorios, etc.)
        action_result = self.actions.handle(
            user_id=uid,
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        ) or {"final": None, "action": None}

        if action_result.get("final"):
            final = action_result["final"]
        action = action_result.get("action")

        # Guardar diálogo
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)

        # Guardar en memoria semántica si procede
        if not is_tech and not is_info:
            self.memory.add_semantic(uid, f"user: {user_msg}")
            self.memory.add_semantic(uid, f"assistant: {final}")

        # Guardar hechos estructurados
        try:
            for f in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, f)
        except Exception:
            pass

        return {
            "final": final,
            "voice_id": base_voice,
            "intent": intent,
            "action": action,
        }

    # ============================================================
    #  INFO QUERY 2.0 (determinístico, no usa LLM)
    # ============================================================

    def _resolve_info(self, uid: str, txt: str) -> str:
        ROLES = {
            "mamá": "madre", "mama": "madre",
            "papá": "padre", "papa": "padre",
            "hermano": "hermano", "hermana": "hermana",
            "abuelo": "abuelo", "abuela": "abuela",
            "tío": "tio", "tio": "tio",
            "tía": "tia", "tia": "tia",
            "novia": "pareja", "pareja": "pareja",
        }

        # Resolver familiar
        for word, role_norm in ROLES.items():
            if word in txt:
                items = self.memory.get_family_by_role(uid, role_norm)
                if items:
                    names = [f.get("name") for f in items if f.get("name")]
                    if len(names) == 1:
                        return f"Tu {role_norm} se llama {names[0]}."
                    elif len(names) > 1:
                        return f"Tus {role_norm}s se llaman: {', '.join(names)}."
                return f"No tengo guardado el nombre de tu {role_norm}. ¿Querés decírmelo?"

        # Resolver mascotas
        if "mascotas" in txt or "animales" in txt or "perros" in txt or "gatos" in txt:
            pets = self.memory.get_pets(uid)
            if not pets:
                return "Todavía no tengo registradas tus mascotas. ¿Querés decirme sus nombres?"
            names = ", ".join([p.get("name") for p in pets if p.get("name")])
            if names:
                return f"Tus mascotas son: {names}."
            return "Tengo registradas mascotas tuyas, pero sin nombres claros. ¿Querés recordármelos?"

        return "Todavía no tengo ese dato guardado. ¿Querés contármelo?"

    # ============================================================
    # LLM (modo general o técnico)
    # ============================================================

    def _llm(self, uid: str, msg: str, ctx: dict, emotion: dict,
             precise: bool = False, no_humor: bool = False) -> str:

        # Memorias
        profile_doc = self.memory.get_user_profile(uid)
        facts_pretty = self.memory.get_all_facts_pretty(uid)
        recent_dialog = self.memory.get_recent_dialog(uid)
        semantic_hits = self.memory.search_semantic(uid, msg)

        prefs = ctx.get("prefs") or {}
        personality_key = prefs.get("personality", "auri_classic")
        sty = self.PERSONALITY.get(personality_key, self.PERSONALITY["auri_classic"])

        if precise:
            sty = {
                "tone": "técnico y directo",
                "emoji": "",
                "length": "corto",
                "voice": "verse",
            }

        overall = emotion.get("overall")
        stress = float(emotion.get("stress", 0.2))

        system_prompt = f"""
Eres Auri, asistente personal emocional y compañero diario del usuario.

[Modo técnico / precisión]
- precise = {precise}
- humor_permitido = {not no_humor}

[Personalidad base]
- Perfil: {personality_key}
- Tono: {sty['tone']} {sty['emoji']}

[Estado emocional aproximado]
- overall: {overall}
- stress: {stress}

[Memoria del usuario]
- Perfil persistente:
{profile_doc}

- Hechos relevantes (facts estructurados):
{facts_pretty}

- Memoria semántica relevante:
{semantic_hits}

- Diálogo reciente:
{recent_dialog}

REGLAS:
1. Nunca inventes datos personales del usuario. Si no estás seguro, decí claramente que no lo sabés y pedí el dato.
2. Si precise = True o la consulta es técnica:
   - Sé conciso, directo y claro.
   - No uses humor ni emojis.
   - Enfócate en la explicación / solución.
3. Si el usuario está emocional (triste, enojado, estresado) y no es una consulta técnica:
   - Validá lo que siente.
   - Sé cálido y respetuoso.
   - NO uses sarcasmo ni humor si humor_permitido = False.
4. Si pregunta por nombres, relaciones o datos personales:
   - Prioriza lo que aparece en la memoria (perfil y facts).
   - Si no aparece, pedí el dato explícitamente y decí que todavía no lo tenés guardado.
5. Sonido general de Auri:
   - Natural, cercano, pero cuidadoso con el estado emocional.
"""

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg},
            ],
        )

        return (resp.output_text or "").strip()

    # ============================================================
    # Auto-aprendizaje familiar simple V2
    # ============================================================

    def _auto_family(self, uid: str, txt: str):
        # Caso 1: "mi tío se llama Oscar"
        m1 = re.search(
            r"mi\s+"
            r"(tío|tio|tía|tia|hermano|hermana|abuelo|abuela|primo|prima|sobrino|sobrina|padre|madre)"
            r"(?:\s+se llama)?\s+([a-záéíóúñ]+)",
            txt,
        )
        if m1:
            role = m1.group(1).lower()
            name = m1.group(2).capitalize()

            self.memory.add_fact_structured(uid, {
                "type": "family_member",
                "role": role,
                "name": name,
                "text": f"{role.capitalize()}: {name}",
                "category": "relationship",
                "importance": 4,
                "confidence": 0.95,
            })

        # Caso 2: "tengo otros tíos llamados Francisco"
        m2_list = re.findall(
            r"(tíos|tios|tías|tias)\s+llamados?\s+([a-záéíóúñ]+)",
            txt,
        )
        for role_raw, name_raw in m2_list:
            role_singular = role_raw.rstrip("s")  # tíos → tío
            name = name_raw.capitalize()

            self.memory.add_fact_structured(uid, {
                "type": "family_member",
                "role": role_singular,
                "name": name,
                "text": f"{role_singular.capitalize()}: {name}",
                "category": "relationship",
                "importance": 3,
                "confidence": 0.90,
            })

    # ----------------------------------------------------------
    # UID DESDE WEBSOCKET — requerido por server.py y STT
    # ----------------------------------------------------------
    def set_user_uid(self, uid: str):
        """
        Compatibilidad con versiones anteriores.
        Asigna el UID al ContextEngine y precarga memoria básica.
        """
        if not uid:
            return

        try:
            # Actualiza el ContextEngine (para que daily_context incluya el UID)
            self.context.set_user_uid(uid)

            # Precarga datos de memoria
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)

            print(f"UID detectado por AuriMind: {uid}")

        except Exception as e:
            print(f"[AuriMindV9.1] Error asignando UID: {e}")


# ----------------------------------------------------------
# Alias de compatibilidad
# ----------------------------------------------------------
AuriMind = AuriMindV9
AuriMindV6 = AuriMindV9
AuriMindV7 = AuriMindV9
AuriMindV8 = AuriMindV9
