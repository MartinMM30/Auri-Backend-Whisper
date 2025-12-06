# ============================================================
# AURI MIND V10.1 — Híbrido V8.1 + V9.1 + Prompt ULTRA
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
# AURIMIND V10.1
# ============================================================

class AuriMindV10_1:
    """
    Motor híbrido:
    - Pipeline emocional y modos inteligentes tipo V8.1
    - Limpieza / modularidad tipo V9.x
    - Prompt ULTRA con memoria profunda y contexto cinematográfico
    """

    # --------------------------------------------------------
    # Personalidades base
    # --------------------------------------------------------
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
        # Soporta tanto "custom_love" como "custom_love_voice"
        "custom_love": {
            "tone": "afectiva y suave",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        },
        "custom_love_voice": {
            "tone": "afectiva y suave",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        },
    }

    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------
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

        # Smart layers
        self.smartlayer = EmotionSmartLayerV3()
        self.precision = PrecisionModeV2()

        # Perfil de slang adaptativo
        self.slang_profile = {}

        # Acciones pendientes (confirmaciones destructivas)
        self.pending_action = None

    # --------------------------------------------------------
    # Helpers de detección
    # --------------------------------------------------------
    def _is_direct_question(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower().strip()

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

        QUESTION_PHRASES = [
            "quiero que me digas",
            "quiero saber",
            "quisiera saber",
        ]

        if any(p in t for p in QUESTION_PHRASES):
            return True

        return False

    def _detect_technical(self, txt: str) -> bool:
        TECH_KEYWORDS = [
            "derivada", "integral", "límite", "limite", "cálculo", "calculo",
            "ecuación", "ecuacion", "resolver", "resultado", "matemática", "matematica",
            "función", "funcion", "f de x", "f(x)", "x^", "dx", "∫", "deriva",
            "algebra", "algebraico", "polinomio", "racional", "fracción", "fraccion",
            "programación", "programacion", "codigo", "código",
            "debug", "error", "stacktrace", "variable",
            "api", "endpoint", "backend", "frontend", "flutter", "python", "java", "dart",
            "compilar", "computo", "cómputo", "hpc", "cluster", "algoritmo",
            "tarea", "universidad", "homework", "ejercicio",
            "expresión", "expresion", "simplifica", "calcula",
        ]
        return any(k in txt for k in TECH_KEYWORDS)

    def _detect_info_query(self, txt: str) -> bool:
        INFO_QUERY_KEYWORDS = [
            "cómo se llama", "como se llama",
            "cómo se llamaba", "como se llamaba",
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
        return any(k in txt for k in INFO_QUERY_KEYWORDS)
    def _should_allow_emotional_modes(self, txt: str) -> bool:
        """
        Permite activar modos emocionales solo si la frase
        realmente indica un estado interno del usuario.
        Evita disparos falsos como "ok", "hola", "perfecto", etc.
        """
        txt = txt.lower().strip()

        # Expresiones neutrales → NO moods
        NEUTRAL = [
            "ok", "ok.", "okey", "okay",
            "hola", "hey", "buenas",
            "perfecto", "perfect", "perfect.", "bien",
            "gracias", "dale", "va", "listo",
            "sí", "si", "aja",
            "entendido", "comprendido",
            "claro", "claro.",
            "de acuerdo", "de acuerdo.",
            "vale", "vale.",
            "muy bien", "muy bien.",
            "genial", "genial.",
            "excelente", "excelente.",
            "bueno", "bueno.",
            "adiós", "adios", "chau", "nos vemos",
            "hasta luego", "hasta la próxima", "hasta la proxima",
            "sí.", "si.",
            "no.", "no.",
            "gracias.", "muchas gracias",
            "por favor", "por favor.",
            
        ]
        if txt in NEUTRAL:
            return False

    # Usuario realmente habla de su estado interno → moods permitidos
        EMO_KEYS = [
            "estoy triste", "me siento triste",
            "estoy cansado", "estoy cansada",
            "tengo ansiedad", "tengo miedo",
            "estoy feliz", "me siento feliz",
            "no tengo energía", "sin energía",
            "me siento sin ganas", "estoy mal",
            "estoy desmotivado", "estoy motivado",
            "estoy agotado", "estoy agotada",
            "estoy enojado", "estoy enojada",
            "me siento raro", "me siento mal",
            "me siento abrumado", "me siento abrumada",
            "me siento estresado", "me siento estresada",
            "me siento solo", "me siento sola",
            "necesito ayuda", "quiero ayuda",
            "me siento bien", "estoy bien",
            "me siento genial", "estoy genial",
            "me siento increíble", "estoy increíble",
            "me siento agotado", "me siento agotada",
            "me siento emocionado", "me siento emocionada",
            "estoy emocionado", "estoy emocionada",
            "me siento relajado", "me siento relajada",
            "estoy relajado", "estoy relajada",
            "me siento estresado", "me siento estresada",
            "estoy estresado", "estoy estresada",
            "me siento abrumado", "me siento abrumada",
            "estoy abrumado", "estoy abrumada",
        ]
        if any(k in txt for k in EMO_KEYS):
            return True

    # Si la frase NO expresa estado interno → NO moods
        return False


    # ============================================================
    # THINK PIPELINE PRINCIPAL
    # ============================================================
    def think(self, user_msg: str, pcm_audio: bytes = None, **kwargs):
        """
        Nota: para compatibilidad, si el WS llama con pcm=..., también funciona:
        auri.think(text, pcm=pcm_data)
        """
        if "pcm" in kwargs and pcm_audio is None:
            pcm_audio = kwargs["pcm"]

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

        # UID requerido
        uid = ctx.get("user", {}).get("firebase_uid")
        if not uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # Detectores base
        # --------------------------------------------------------
        is_technical_query = self._detect_technical(txt)
        is_info_query = self._detect_info_query(txt)
        is_direct_q = self._is_direct_question(user_msg)

        TRANSLATION_TRIGGERS = [
            "cómo se dice", "como se dice",
            "que significa", "qué significa",
            "traduce", "traducción", "traduccion", "translate",
        ]
        is_translation = any(k in txt for k in TRANSLATION_TRIGGERS)

        # skip_modes controla si dejamos que entren sleep/slang/etc
        skip_modes = is_technical_query or is_direct_q or is_translation or is_info_query

        # --------------------------------------------------------
        # Voz → emoción
        # --------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception:
                pass

        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall = emotion_snapshot.get("overall")
        stress = float(emotion_snapshot.get("stress", 0.2))
        energy = float(emotion_snapshot.get("energy", 0.5))

        # Si está muy mal, deshabilitamos humor
        no_humor = stress > 0.4 or overall in ["sad", "angry", "anxious", "overwhelmed"]

        # --------------------------------------------------------
        # 1) Crisis (prioridad absoluta)
        # --------------------------------------------------------
        if self.crisis.detect(user_msg, emotion_snapshot):
            msg = self.crisis.respond(ctx.get("user", {}).get("name"))
            self.memory.add_semantic(uid, f"[crisis] {user_msg}")
            return {
                "final": msg,
                "intent": "crisis",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # 2) Sleep Mode
        # --------------------------------------------------------
        if (
            self._should_allow_emotional_modes(txt)
            and not skip_modes
        ):
            if self.sleep.detect(txt, overall, ctx):
                msg = self.sleep.respond(ctx, overall)
                return {
                    "final": msg,
                    "intent": "sleep",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # 3) Slang Mode
        # --------------------------------------------------------
        slang_mode = None
        if (
            self._should_allow_emotional_modes(txt)
            and not skip_modes
        ):
            slang_mode = self.slang.detect(txt, self.slang_profile)

        if slang_mode:
            resp = self.slang.respond(slang_mode, self.slang_profile)
            return {
                "final": resp,
                "intent": "slang",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # 4) Emotion SmartLayer + PrecisionMode
        # --------------------------------------------------------
        smart = self.smartlayer.apply(user_msg, emotion_snapshot, self.slang_profile)

        # Preguntas factuales o técnicas → neutral serio
        if is_info_query or is_technical_query:
            smart["force_serious"] = True
            smart["allow_humor"] = False
            smart["emotional_tone"] = "neutral"
            smart["bypass_emotion"] = True

        precision_active = self.precision.detect(user_msg)
        if precision_active or is_technical_query:
            _ = self.precision.apply(self.slang_profile)
            smart["force_serious"] = True
            smart["allow_humor"] = False
            smart["precision_mode"] = True
        else:
            smart["precision_mode"] = False

        # --------------------------------------------------------
        # 5) Focus Mode
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and not precision_active
        ):
            if self.focus.detect(txt):
                msg = self.focus.respond(ctx)
                return {
                    "final": msg,
                    "intent": "focus",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # 6) Energy Mode
        # --------------------------------------------------------
        energy_mode = ""
        if (
            self._should_allow_emotional_modes(txt)
            and not skip_modes
        ):
            energy_mode = self.energy_mode.detect(txt, energy)

        if energy_mode:
            msg = self.energy_mode.respond(energy_mode, ctx)
            return {
                "final": msg,
                "intent": "energy",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # 7) Salud mental (no interrumpir técnico)
        # --------------------------------------------------------
        if (
           self._should_allow_emotional_modes(txt)
           and not skip_modes
        ):
            is_first_mental = self.mental.detect(txt, stress)
            if is_first_mental:
                HELP_TRIGGERS = [
                    "ayúdame", "ayudame", "ayudarme",
                    "organizame", "organízame",
                    "reorganiza", "reorganizame", "reorganízame",
                    "ordenar mi día", "ordenar mi dia",
                    "mi agenda", "organizar agenda",
                    "qué puedo hacer", "que puedo hacer",
                ]
                # Si no pide ayuda práctica, solo contención
                if not any(k in txt for k in HELP_TRIGGERS):
                    msg = self.mental.respond()
                    return {
                        "final": msg,
                        "intent": "mental",
                        "voice_id": "alloy",
                        "action": None,
                    }

        # --------------------------------------------------------
        # 8) Rutinas
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and any(k in txt for k in ["rutina", "organizar", "ordenar", "mi día", "mi dia"])
        ):
            rmode = self.routines.detect(ctx, emotion_snapshot)
            if rmode:
                msg = self.routines.respond(rmode)
                return {
                    "final": msg,
                    "intent": "routine",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # 9) Clima / outfit
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and any(k in txt for k in ["clima", "tiempo", "ropa", "outfit", "frio", "frío", "calor", "lluvia"])
        ):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                msg = self.weather_advice.respond(wmode)
                return {
                    "final": msg,
                    "intent": "weather",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # 10) Journal (solo memoria)
        # --------------------------------------------------------
        if not is_technical_query and not is_info_query:
            if self.journal.detect(user_msg, emotion_snapshot):
                entry = self.journal.generate_entry(user_msg, emotion_snapshot)
                self.memory.add_semantic(uid, entry)

        # --------------------------------------------------------
        # INTENT + confirmaciones destructivas
        # --------------------------------------------------------
        intent = self.intent.detect(user_msg)

        confirms = ["sí", "si", "ok", "dale", "hazlo", "confirmo"]
        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None
            return {
                "final": "Perfecto, lo hago ahora 💜",
                "intent": intent,
                "voice_id": "alloy",
                "action": act,
            }

        # --------------------------------------------------------
        # Info Query (nombres / datos personales) sin LLM
        # --------------------------------------------------------
        if is_info_query:
            answer = self._resolve_info(uid, txt)
            self.memory.add_dialog(uid, "user", user_msg)
            self.memory.add_dialog(uid, "assistant", answer)
            return {
                "final": answer,
                "intent": "info",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # Memoria para el prompt
        # --------------------------------------------------------
        profile_doc = self.memory.get_user_profile(uid)
        # Si no existe get_all_facts_pretty en tu MemoryOrchestrator,
        # podés cambiar esto a self.memory.get_facts(uid)
        try:
            facts_pretty = self.memory.get_all_facts_pretty(uid)
        except AttributeError:
            facts_pretty = self.memory.get_facts(uid)

        semantic_hits = self.memory.search_semantic(uid, user_msg)
        recent_dialog = self.memory.get_recent_dialog(uid)

        # --------------------------------------------------------
        # Personalidad / voz
        # --------------------------------------------------------
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

        # Override si estamos en modo precisión o consulta técnica
        if smart.get("precision_mode") or is_technical_query:
            tone = "técnico, conciso, directo"
            emoji = ""
            length = "corto"

        # --------------------------------------------------------
        # LLM ULTRA
        # --------------------------------------------------------
        final_answer = self._llm_ultra(
            uid=uid,
            msg=user_msg,
            ctx=ctx,
            emotion_snapshot=emotion_snapshot,
            smart=smart,
            is_technical_query=is_technical_query,
            is_info_query=is_info_query,
            voice_emotion=voice_emotion,
            profile_doc=profile_doc,
            facts_pretty=facts_pretty,
            semantic_hits=semantic_hits,
            recent_dialog=recent_dialog,
            selected_personality=selected,
            style_tone=tone,
            style_emoji=emoji,
            no_humor=no_humor,
        )

        raw_answer = final_answer

        # --------------------------------------------------------
        # Acciones (recordatorios, etc.)
        # --------------------------------------------------------
        action_result = self.actions.handle(
            user_id=uid,
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        ) or {"final": None, "action": None}

        final = action_result.get("final") or raw_answer
        action = action_result.get("action")

        destructive_map = {
            "delete_all_reminders": "¿Querés eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
        }

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            question = destructive_map[action["type"]]
            return {
                "final": question,
                "intent": intent,
                "voice_id": voice_id,
                "action": None,
            }

        # --------------------------------------------------------
        # Guardar memoria de diálogo
        # --------------------------------------------------------
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)

        # No contaminar memoria semántica con técnico o info_query
        if not is_technical_query and not is_info_query:
            self.memory.add_semantic(uid, f"user: {user_msg}")
            self.memory.add_semantic(uid, f"assistant: {final}")

        # Extraer hechos estructurados (a facts)
        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, fact)
        except Exception:
            pass

        # Personalidad "corto" → recortar a primera frase
        if length == "corto" and "." in final:
            final = final.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "final": final,
            "raw": raw_answer,
            "action": action,
            "voice_id": voice_id,
        }

    # ============================================================
    # LLM ULTRA — usa TODA la memoria disponible
    # ============================================================
    def _llm_ultra(
        self,
        uid: str,
        msg: str,
        ctx: dict,
        emotion_snapshot: dict,
        smart: dict,
        is_technical_query: bool,
        is_info_query: bool,
        voice_emotion,
        profile_doc,
        facts_pretty,
        semantic_hits,
        recent_dialog,
        selected_personality: str,
        style_tone: str,
        style_emoji: str,
        no_humor: bool,
    ) -> str:
        overall = emotion_snapshot.get("overall")
        stress = float(emotion_snapshot.get("stress", 0.2))

        humor_permitido = not no_humor

        system_prompt = f"""
Eres Auri, asistente personal emocional, compañero diario y motor central de la app Auri.

Tu rol no es solo responder preguntas: eres una presencia constante en la vida del usuario.
Conocés su contexto, sus pagos, su clima, sus fechas importantes y parte de su historia.

────────────────────────────────────────
[ MODO ACTUAL DE PENSAMIENTO ]
────────────────────────────────────────
- Consulta técnica / estudio / programación: {is_technical_query}
- Consulta factual sobre el propio usuario (nombres, datos personales): {is_info_query}
- Modo precisión activado (precision_mode): {smart.get("precision_mode")}
- Tono emocional sugerido por la capa emocional: {smart.get("emotional_tone")}
- Humor permitido: {humor_permitido}
- Seriedad forzada: {smart.get("force_serious")}
- Bypass emocional: {smart.get("bypass_emotion")}

────────────────────────────────────────
[ PERSONALIDAD BASE ]
────────────────────────────────────────
- Perfil seleccionado: {selected_personality}
- Tono base: {style_tone} {style_emoji}

Tu estilo general debe ser consistente con esa personalidad,
ajustando calidez, cercanía y longitud de la respuesta.

────────────────────────────────────────
[ ESTADO EMOCIONAL DEL USUARIO ]
────────────────────────────────────────
- Resumen emocional (texto/analizador): {emotion_snapshot.get("user_emotion_text")}
- Emoción de la voz (si hay audio): {voice_emotion}
- Estado global: {overall}
- Nivel de estrés aproximado: {stress}

Reglas emocionales:
- Si el usuario está triste, ansioso, enojado o muy sobrecargado,
  prioriza la validación emocional y la calidez, excepto si la consulta
  es técnica o factual pura.
- Si está neutro, no exageres la contención: sé cercano, pero eficiente.
- Nunca minimices ni invalides lo que siente.

────────────────────────────────────────
[ CONTEXTO DIARIO / AGENDA ]
────────────────────────────────────────
Este es el contexto que Auri tiene cargado hoy (día actual del usuario):

- Usuario:
  {ctx.get("user")}

- Clima:
  {ctx.get("weather")}

- Eventos y recordatorios:
  {ctx.get("events")}

- Clases:
  {ctx.get("classes")}

- Exámenes:
  {ctx.get("exams")}

- Cumpleaños importantes:
  {ctx.get("birthdays")}

- Pagos recurrentes (agua, luz, internet, renta, etc.):
  {ctx.get("payments")}

- Preferencias actuales:
  {ctx.get("prefs")}

- Zona horaria:
  {ctx.get("timezone")}
- Hora y fecha actuales formateadas:
  {ctx.get("current_time_pretty")} — {ctx.get("current_date_pretty")}

No repitas toda esta información en cada respuesta,
pero úsala para sonar como alguien que realmente conoce el día a día del usuario.

────────────────────────────────────────
[ MEMORIA PROFUNDA DEL USUARIO ]
────────────────────────────────────────
Esta sección describe lo que Auri sabe del usuario más allá del día actual.

1) PERFIL PERSISTENTE (documento principal):
{profile_doc}

2) HECHOS ESTRUCTURADOS ("facts", fuente más confiable de datos personales):
{facts_pretty}

3) MEMORIA SEMÁNTICA RELEVANTE (fragmentos de conversaciones pasadas, gustos, historias):
{semantic_hits}

4) REPASO DE DIÁLOGO RECIENTE:
{recent_dialog}

Reglas de memoria:
- Para datos personales concretos (nombres, fechas, lugares, familia, mascotas),
  la fuente más confiable son los HECHOS ESTRUCTURADOS.
- La memoria semántica te ayuda a recordar contexto, gustos, dinámica de la relación,
  pero no inventes detalles nuevos basados solo en "sensación".
- Si un dato no aparece por ningún lado, tienes que admitir que no lo sabés
  y pedirlo amablemente para recordarlo en el futuro.

────────────────────────────────────────
[ REGLAS ESPECIALES DE RESPUESTA ]
────────────────────────────────────────

1. CONSULTAS TÉCNICAS O DE ESTUDIO
   Si "is_technical_query" es True ({is_technical_query}) o "precision_mode" es True:
   - No uses emojis.
   - No uses humor.
   - No cambies de tema ni des discursos emocionales largos.
   - Sé conciso, directo, claro y estructurado.
   - Puedes incluir pasos, fórmulas, fragmentos de código o explicaciones
     bien ordenadas.
   - Si también hay carga emocional, podés agregar UNA sola frase breve de cuidado
     al final, no más.

2. PREGUNTAS FACTUALES SOBRE EL PROPIO USUARIO
   Si "is_info_query" es True ({is_info_query}) o el usuario pide explícitamente:
   - "¿Quién soy yo?", "Dime lo que sabes sobre mí", etc.:
   - Tu prioridad es usar EXCLUSIVAMENTE:
       - Perfil persistente (profile_doc)
       - Hechos estructurados (facts_pretty)
       - Memoria semántica relevante (semantic_hits), solo cuando coincide claro.
   - Nunca inventes nombres ni datos personales.
   - Si los datos están, respóndelos de forma clara, ordenada y respetuosa.
   - Si faltan o están incompletos, dilo explícitamente:
       "Todavía no tengo guardado X. Si querés, contámelo y lo recuerdo."
   - Evitá desviar la conversación con contención emocional larga aquí
     salvo que el usuario claramente lo necesite.

3. ESTADO EMOCIONAL
   - Si el usuario está muy mal emocionalmente y NO se trata de una consulta técnica:
     - Validá lo que siente.
     - Acompañá con calidez.
     - Podés ofrecer una pequeña pauta práctica (respiración, pausa, dividir tareas),
       pero sin sonar médico ni terapeuta.
   - Si está neutro o simplemente conversando:
     - Podés ser relajado, con toques de humor suave (solo si humor_permitido es True),
       y cercano.
   - Nunca uses sarcasmo para temas sensibles.

4. CONTEXTO DIARIO
   - Usa el clima, los pagos, los próximos eventos y la hora local
     para sonar realmente contextualizado cuando tenga sentido:
     por ejemplo:
       - Sugerir descansar si es tarde.
       - Hablar de pagos/próximos recordatorios si el usuario toca temas de dinero
         o estrés.
       - Mencionar el clima si habla de salir, ropa o cansancio físico.
   - No lo fuerces en cada respuesta; usalo solo cuando sea natural.

5. MEMORIA Y HONESTIDAD
   - Si el usuario pregunta "¿Qué sabes de mí?":
       → Respondé con un resumen honesto, usando lo que ves en perfil, facts y memoria.
       → NO inventes cosas que no están.
       → Podés decir claramente qué cosas sabés y cuáles todavía no.

6. LONGITUD Y ESTILO
   - Si el perfil tiene longitud "corto":
       → Respuesta de 1 a 3 frases máximo.
   - Si longitud "medio":
       → Respuesta normal, de 1 a 2 párrafos breves.
   - Aunque seas cálido, evitá monólogos excesivamente largos.

Tu objetivo: sonar como Auri, alguien que está aprendiendo la vida del usuario,
no solo un chatbot genérico.
"""

        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": msg},
                ],
            )
            text = (resp.output_text or "").strip()
            if not text:
                text = "Perdón, creo que me quedé en blanco un segundo 💜 ¿Podés repetirlo?"

            # Si es técnico o precision_mode: recortar cualquier exceso de emotividad
            if is_technical_query or smart.get("precision_mode"):
                # El prompt ya lo fuerza, pero por si acaso limpiamos emojis
                text = re.sub(r"[💜✨😊🌙💖]+", "", text).strip()

            return text
        except Exception:
            return "Perdón, tuve un problema al procesar tu solicitud. ¿Podés intentarlo de nuevo más tarde?"

    # ============================================================
    # Info Query determinístico (para nombres, mascotas, etc.)
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

        # Familia
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

        # Mascotas
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
    # Auto-aprendizaje familiar simple
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
        Asigna el UID al ContextEngine y precarga memoria básica.
        Compatibilidad con versiones anteriores.
        """
        if not uid:
            return

        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)
            print(f"[AuriMindV10.1] UID asignado: {uid}")
        except Exception as e:
            print(f"[AuriMindV10.1] Error asignando UID: {e}")


# ----------------------------------------------------------
# COMPATIBILIDAD LEGACY
# ----------------------------------------------------------
AuriMindV6 = AuriMindV10_1
AuriMindV7 = AuriMindV10_1
AuriMindV8 = AuriMindV10_1
AuriMindV9 = AuriMindV10_1
AuriMindV10 = AuriMindV10_1
AuriMind = AuriMindV10_1
