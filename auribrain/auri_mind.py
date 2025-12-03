# ============================================================
# AURI MIND V7.6 — Motor emocional + modos inteligentes + precisión
# ============================================================

from openai import OpenAI

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

# Nuevos módulos V7.5 / V7.6
from auribrain.emotion_smartlayer_v3 import EmotionSmartLayerV3
from auribrain.precision_mode_v2 import PrecisionModeV2


# ============================================================
# AURI MIND 7.6
# ============================================================

class AuriMindV7_6:

    PERSONALITY_PRESETS = {
        "auri_classic": {
            "tone": "cálido y profesional",
            "emoji": "💜",
            "length": "medio",
            "voice_id": "alloy",
        },
        "soft": {
            "tone": "suave y calmado",
            "emoji": "🌙",
            "length": "corto",
            "voice_id": "nova",
        },
        "siri_style": {
            "tone": "formal, educado",
            "emoji": "",
            "length": "corto",
            "voice_id": "verse",
        },
        "anime_soft": {
            "tone": "dulce y expresiva",
            "emoji": "✨",
            "length": "medio",
            "voice_id": "hikari",
        },
        "professional": {
            "tone": "serio",
            "emoji": "",
            "length": "medio",
            "voice_id": "amber",
        },
        "friendly": {
            "tone": "amigable",
            "emoji": "😊",
            "length": "medio",
            "voice_id": "alloy",
        },
        "custom_love_voice": {
            "tone": "afectiva y suave",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        },
    }

    # ----------------------------------------------------------
    # INIT
    # ----------------------------------------------------------
    def __init__(self):
        self.client = OpenAI()

        # Motores base
        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # Modos especiales
        self.crisis = CrisisEngine()
        self.sleep = SleepEngine()
        self.love = LoveModeEngine()
        self.energy_mode = EnergyEngine()
        self.slang = SlangModeEngine()
        self.focus = FocusEngine()
        self.journal = JournalEngine()
        self.mental = MentalHealthEngine()
        self.routines = RoutineEngine()
        self.weather_advice = WeatherAdviceEngine()

        # NUEVOS MODOS V7.5 / V7.6
        self.smartlayer = EmotionSmartLayerV3()
        self.precision = PrecisionModeV2()

        # Perfil de slang adaptativo
        self.slang_profile = {}

        # Acciones pendientes (confirmaciones destructivas)
        self.pending_action = None

    # ----------------------------------------------------------
    # Helper: detectar si es pregunta directa
    # ----------------------------------------------------------
    def _is_direct_question(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower().strip()

        # Tiene signo de pregunta → claramente pregunta
        if "?" in t:
            return True

        STARTS = [
            "qué", "que",
            "cómo", "como",
            "cuándo", "cuando",
            "dónde", "donde",
            "por qué", "porque",
            "quién", "quien",
            "cuál", "cual",
            "what", "how",
            "why", "who", "when",
            "dime", "decime",
            "explícame", "explicame",
            "enséñame", "enseñame",
        ]

        if any(t.startswith(s) for s in STARTS):
            return True

        # Preguntas implícitas tipo "quiero que me digas..."
        QUESTION_PHRASES = [
            "quiero que me digas",
            "quiero saber",
            "quisiera saber",
        ]

        if any(p in t for p in QUESTION_PHRASES):
            return True

        return False

    # ----------------------------------------------------------
    # THINK PIPELINE
    # ----------------------------------------------------------
    def think(self, user_msg: str, pcm_audio: bytes = None):
        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {
                "final": "No escuché nada, ¿podés repetirlo?",
                "intent": "unknown",
                "voice_id": "alloy",
                "action": None,
            }

        if not self.context.is_ready():
            return {
                "final": "Dame un momento… estoy cargando tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
                "action": None,
            }

        ctx = self.context.get_daily_context()
        txt = user_msg.lower()

        # ↓↓↓ CONTROL DE MODOS ESPECIALES
        skip_modes = self._is_direct_question(user_msg)

        # Traducción / definición → desactivar automáticos
        TRANSLATION_TRIGGERS = [
            "cómo se dice", "como se dice",
            "que significa", "qué significa",
            "traduce", "traducción", "translate",
        ]
        if any(k in txt for k in TRANSLATION_TRIGGERS):
            skip_modes = True

        # ----------------------------------------------------------
        # INFO QUERY BYPASS (bloquea modos automáticos)
        # ----------------------------------------------------------
        INFO_QUERY_KEYWORDS = [
            "cómo se llama", "como se llama",
            "cómo se llaman", "como se llaman",
            "mis mascotas", "mis animales",
            "mis perros", "mis gatos",
            "mis padres", "mi mamá", "mi mama", "mi papá", "mi papa",
            "nombre de mis", "nombres de mis",
            "nombre de mi", "nombres de mi",
            "dime el nombre de",
            "quiero que me digas",
            "quiero saber el nombre",
            "cuál es el nombre", "cual es el nombre",
        ]
        is_info_query = any(k in txt for k in INFO_QUERY_KEYWORDS)
        if is_info_query:
            # Si es pregunta factual → NO disparar modos automáticos
            skip_modes = True

        # ------------------------------------------
        # Voz → emoción
        # ------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception:
                pass

        # Emoción total
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall = emotion_snapshot.get("overall")
        stress = float(emotion_snapshot.get("stress", 0.2))
        energy = float(emotion_snapshot.get("energy", 0.5))
        affection = float(emotion_snapshot.get("affection", 0.4))

        # ------------------------------------------
        # UID requerido
        # ------------------------------------------
        uid = ctx.get("user", {}).get("firebase_uid")
        if not uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 1) CRISIS MODE (prioridad máxima)
        # =======================================================
        if self.crisis.detect(user_msg, emotion_snapshot):
            msg = self.crisis.respond(ctx.get("user", {}).get("name"))
            self.memory.add_semantic(uid, f"[crisis] {user_msg}")
            return {
                "final": msg,
                "raw": msg,
                "intent": "crisis",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 2) SLEEP MODE
        # =======================================================
        if not skip_modes and not is_info_query and self.sleep.detect(txt, overall, ctx):
            msg = self.sleep.respond(ctx, overall)
            return {
                "final": msg,
                "raw": msg,
                "intent": "sleep",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 3) SLANG MODE V4
        # =======================================================
        slang_mode = None
        if not skip_modes and not is_info_query:
            slang_mode = self.slang.detect(txt, self.slang_profile)

        if slang_mode:
            resp = self.slang.respond(slang_mode, self.slang_profile)
            return {
                "final": resp,
                "raw": resp,
                "intent": "slang",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 4) EMOTION SMARTLAYER V3
        # =======================================================
        smart = self.smartlayer.apply(user_msg, emotion_snapshot, self.slang_profile)

        # BYPASS de contención emocional para preguntas factuales
        if is_info_query:
            smart["force_serious"] = True
            smart["allow_humor"] = False
            smart["emotional_tone"] = "neutral"
            smart["bypass_emotion"] = True

        # =======================================================
        # 🔥 5) PRECISION MODE V2
        # =======================================================
        precision_active = self.precision.detect(user_msg)
        if precision_active:
            _ = self.precision.apply(self.slang_profile)
            smart["force_serious"] = True
            smart["allow_humor"] = False
            smart["precision_mode"] = True
        else:
            smart["precision_mode"] = False

        # =======================================================
        # 🔥 6) FOCUS MODE
        # =======================================================
        if not skip_modes and not is_info_query and self.focus.detect(txt):
            msg = self.focus.respond(ctx)
            return {
                "final": msg,
                "raw": msg,
                "intent": "focus",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 7) ENERGY MODE
        # =======================================================
        energy_mode = ""
        if not skip_modes and not precision_active and not is_info_query:
            energy_mode = self.energy_mode.detect(txt, energy)

        if energy_mode:
            msg = self.energy_mode.respond(energy_mode, ctx)
            return {
                "final": msg,
                "raw": msg,
                "intent": "energy",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 8) SALUD MENTAL
        # =======================================================
        if not skip_modes and not is_info_query and self.mental.detect(txt, stress):
            msg = self.mental.respond()
            return {
                "final": msg,
                "raw": msg,
                "intent": "mental",
                "voice_id": "alloy",
                "action": None,
            }

        # =======================================================
        # 🔥 9) RUTINAS
        # =======================================================
        if (
            not skip_modes
            and not is_info_query
            and any(k in txt for k in ["rutina", "organizar", "ordenar", "mi día", "mi dia"])
        ):
            rmode = self.routines.detect(ctx, emotion_snapshot)
            if rmode:
                msg = self.routines.respond(rmode)
                return {
                    "final": msg,
                    "raw": msg,
                    "intent": "routine",
                    "voice_id": "alloy",
                    "action": None,
                }

        # =======================================================
        # 🔥 10) CLIMA / OUTFIT
        # =======================================================
        if (
            not skip_modes
            and not is_info_query
            and any(k in txt for k in ["clima", "tiempo", "ropa", "outfit", "frio", "calor", "lluvia"])
        ):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                msg = self.weather_advice.respond(wmode)
                return {
                    "final": msg,
                    "raw": msg,
                    "intent": "weather",
                    "voice_id": "alloy",
                    "action": None,
                }

        # =======================================================
        # JOURNAL (solo efecto de memoria, no cambia respuesta)
        # =======================================================
        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(uid, entry)

        # =======================================================
        # LLM PIPELINE
        # =======================================================
        intent = self.intent.detect(user_msg)

        profile = self.memory.get_user_profile(uid)
        long_facts = self.memory.get_facts(uid)
        semantic = self.memory.search_semantic(uid, user_msg)
        recent = self.memory.get_recent_dialog(uid)

        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(
            selected,
            self.PERSONALITY_PRESETS["auri_classic"],
        )

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # Override personalidad si está en modo precisión
        if smart.get("precision_mode"):
            tone = "técnico, conciso, directo"
            emoji = ""
            length = "corto"

        # =======================================================
        # SYSTEM PROMPT FINAL
        # =======================================================
        system_prompt = f"""
Eres Auri, asistente personal emocional.

Modo técnico: {smart.get("precision_mode")}
Tono emocional: {smart.get("emotional_tone")}
Humor permitido: {smart.get("allow_humor")}
Seriedad obligatoria: {smart.get("force_serious")}

Personalidad seleccionada: {selected}
Tono base: {tone} {emoji}

Emoción del usuario (texto): {emotion_snapshot.get("user_emotion_text")}
Emoción del usuario (voz): {voice_emotion}
Estado general del usuario: {overall}

Perfil persistente del usuario:
{profile}

Hechos relevantes:
{long_facts}

Memoria contextual:
{semantic}

Conversación reciente:
{recent}

Reglas:
- Si precision_mode = True → NO usar emojis, NO usar humor, NO usar jerga.
- Responder siempre adaptándote a la emoción del usuario.
- Ser clara, cálida o técnica según el caso.
"""

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # =======================================================
        # ACCIONES
        # =======================================================
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        ) or {"final": None, "action": None}

        final = action_result.get("final") or raw_answer
        action = action_result.get("action")

        # Confirmaciones destructivas
        confirms = ["sí", "si", "ok", "dale", "hazlo", "confirmo"]
        destructive_map = {
            "delete_all_reminders": "¿Querés eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
        }

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None
            return {
                "final": "Perfecto, lo hago ahora 💜",
                "raw": final,
                "intent": intent,
                "voice_id": voice_id,
                "action": act,
            }

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            return {
                "final": destructive_map[action["type"]],
                "raw": destructive_map[action["type"]],
                "intent": intent,
                "voice_id": voice_id,
                "action": None,
            }

        # Guardar memoria
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)
        self.memory.add_semantic(uid, f"user: {user_msg}")
        self.memory.add_semantic(uid, f"assistant: {final}")

        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, fact)
        except Exception:
            pass

        # Personalidad corta → respuesta breve
        if length == "corto" and "." in final:
            final = final.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final,
            "action": action,
            "voice_id": voice_id,
        }

    # ----------------------------------------------------------
    # UID DESDE WEBSOCKET
    # ----------------------------------------------------------
    def set_user_uid(self, uid: str):
        if not uid:
            return
        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)
            print(f"UID detectado por AuriMind: {uid}")
        except Exception as e:
            print(f"[AuriMind] Error asignando UID: {e}")


# ----------------------------------------------------------
# COMPATIBILIDAD LEGACY
# ----------------------------------------------------------
AuriMindV6 = AuriMindV7_6
AuriMindV7 = AuriMindV7_6
AuriMindV7_5 = AuriMindV7_6
AuriMind = AuriMindV7_6
