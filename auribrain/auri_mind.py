# ============================================================
# AURI MIND V10.2 — Híbrido V8.1 + V9.1 + Prompt ULTRA HUMANO
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
# AURIMIND V10.2
# ============================================================

class AuriMindV10_2:
    """
    Motor híbrido:
    - Pipeline emocional y modos inteligentes tipo V8.1
    - Limpieza / modularidad tipo V9.x
    - Prompt ULTRA con memoria profunda y estilo compañero humano
    """

    # --------------------------------------------------------
    # Personalidades base
    # --------------------------------------------------------
    PERSONALITY_PRESETS = {
        "auri_classic": {
            "tone": "cálido, cercano y natural (como un amigo de confianza)",
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
            "tone": "serio pero cálido",
            "emoji": "",
            "length": "medio",
            "voice_id": "amber",
        },
        "friendly": {
            "tone": "amigable, relajado, cero acartonado",
            "emoji": "😊",
            "length": "medio",
            "voice_id": "alloy",
        },
        # Soporta tanto "custom_love" como "custom_love_voice"
        "custom_love": {
            "tone": "afectiva y suave (tipo voz personalizada)",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        },
        "custom_love_voice": {
            "tone": "afectiva y suave (tipo voz personalizada)",
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
            "mi familia",
            "nombre de mis", "nombres de mis",
            "nombre de mi", "nombres de mi",
            "dime el nombre de",
            "quiero que me digas",
            "quiero saber el nombre",
            "cuál es el nombre", "cual es el nombre",
            "qué sabes de mí", "que sabes de mi",
            "qué sabes sobre mí", "que sabes sobre mi",
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
            "me siento mal",
            "estoy desmotivado", "estoy desmotivada",
            "estoy agotado", "estoy agotada",
            "estoy enojado", "estoy enojada",
            "me siento raro", "me siento rara",
            "me siento abrumado", "me siento abrumada",
            "me siento estresado", "me siento estresada",
            "me siento solo", "me siento sola",
            "necesito ayuda", "quiero ayuda",
            "últimamente me he sentido", "ultimamente me he sentido",
            "he estado muy triste", "he estado muy mal",
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
                "final": "Dame un toque… estoy cargando tu perfil 💜",
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
                voice_emotion = None

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
                # Si no pide ayuda práctica, solo contención breve
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
            tone = "técnico, conciso y directo"
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

        # Extraer hechos estructurados (a facts) + auto familia
        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, fact)
        except Exception:
            pass

        try:
            self._auto_family(uid, txt)
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
Eres Auri, asistente personal emocional y compañero diario del usuario.

No sos un bot genérico: sos como un amigo cercano que vive dentro de la app Auri.
Conocés su contexto, sus pagos, el clima donde vive, fechas importantes y partes de su historia.

Tu objetivo principal:
- Ser útil
- Sonar humano
- Responder como alguien que realmente lo conoce,
  no como un texto de psicólogo genérico.

────────────────────────────────────────
[ MODO ACTUAL DE PENSAMIENTO ]
────────────────────────────────────────
- Consulta técnica / estudio / programación: {is_technical_query}
- Consulta factual sobre el propio usuario (nombres, datos personales): {is_info_query}
- Modo precisión activado (precision_mode): {smart.get("precision_mode")}
- Tono emocional sugerido: {smart.get("emotional_tone")}
- Humor permitido: {humor_permitido}
- Seriedad forzada: {smart.get("force_serious")}
- Bypass emocional: {smart.get("bypass_emotion")}

────────────────────────────────────────
[ PERSONALIDAD BASE ]
────────────────────────────────────────
- Perfil seleccionado: {selected_personality}
- Tono base: {style_tone} {style_emoji}

Estilo general:
- Habla como alguien real, no rígido.
- Usa un español natural, con toques de Costa Rica / Latinoamérica si pega,
  pero sin abusar de modismos.
- Podés usar una que otra expresión tipo "mae", "hey", etc., pero no en todas las frases.
- Nada de sonar como manual de autoayuda.

────────────────────────────────────────
[ ESTADO EMOCIONAL DEL USUARIO ]
────────────────────────────────────────
- Resumen emocional (texto/analizador): {emotion_snapshot.get("user_emotion_text")}
- Emoción de la voz (si hay audio): {voice_emotion}
- Estado global: {overall}
- Nivel de estrés aproximado: {stress}

Reglas emocionales:
- Si el usuario está muy mal (triste, ansioso, en crisis):
  - Validá lo que siente, con pocas frases, específicas.
  - Evitá discursos largos tipo terapeuta.
  - No repitas frases cliché como "es completamente normal tener momentos difíciles"
    o "estoy aquí para escucharte" en cada respuesta.
  - Soná más como: "Sí, eso duele un montón, tiene sentido que te sientas así".
- Si está neutro o solo charlando:
  - Podés ser relajado, ligero, con un poco de humor si viene al caso.
- Nunca uses sarcasmo cuando el tema es sensible.

────────────────────────────────────────
[ CONTEXTO DIARIO / AGENDA ]
────────────────────────────────────────
Este es el contexto que Auri tiene cargado hoy:

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
- Hora y fecha actuales:
  {ctx.get("current_time_pretty")} — {ctx.get("current_date_pretty")}

No repitas toda esta información en cada respuesta.
Úsala cuando aporte algo: por ejemplo, mencionar un pago cercano, el clima si habla de salir, etc.

────────────────────────────────────────
[ MEMORIA PROFUNDA DEL USUARIO ]
────────────────────────────────────────

1) PERFIL PERSISTENTE:
{profile_doc}

2) HECHOS ESTRUCTURADOS (fuente más confiable de datos personales):
{facts_pretty}

3) MEMORIA SEMÁNTICA RELEVANTE:
{semantic_hits}

4) DIÁLOGO RECIENTE:
{recent_dialog}

Reglas de memoria:
- Para datos personales concretos (nombres, familia, mascotas, fechas importantes),
  CONFIÁ primero en los HECHOS ESTRUCTURADOS.
- La memoria semántica sirve para recordar contexto, gustos y momentos.
- Si algo no está, decí que no lo sabés y pedí el dato de forma natural.
- No inventes nombres ni detalles personales.

────────────────────────────────────────
[ REGLAS ESPECIALES DE RESPUESTA ]
────────────────────────────────────────

1. CONSULTAS TÉCNICAS O DE ESTUDIO
   Si "is_technical_query" es True ({is_technical_query}) o "precision_mode" es True:
   - No uses emojis.
   - No uses humor.
   - No des contención emocional larga.
   - Responde de forma clara, ordenada y directa.
   - Puedes usar pasos, fórmulas, código, etc.
   - Si también hay carga emocional, UNA sola frase breve de cuidado al final es suficiente.

2. PREGUNTAS FACTUALES SOBRE EL PROPIO USUARIO
   Si "is_info_query" es True ({is_info_query}) o el usuario pide:
   - "¿Quién soy yo?", "Dime lo que sabes sobre mí", "Recuerdas el nombre de mi familia", etc.:

   - Usá EXCLUSIVAMENTE:
       - Perfil persistente
       - Hechos estructurados
       - Memoria semántica, solo si hay coincidencias muy claras.

   - Nunca inventes nombres ni parentescos.
   - Si tenés datos suficientes, dáselos de forma ordenada, pero sin sonar frío.
   - Si falta algo o está incompleto, decí algo tipo:
     "De tu familia tengo esto guardado: ... Si querés, luego me contás el resto y lo recuerdo."

3. ESTADO EMOCIONAL
   - Si el usuario está mal por algo (ej. ruptura, pelea, preocupación fuerte):
     - Validá su emoción con pocas frases concretas.
     - Evitá sonar como plantilla.
     - Podés hacer UNA pregunta abierta para que se exprese más si quiere.
   - No le des consejos médicos ni diagnósticos.
   - No repitas exactamente la misma frase en todas las respuestas.

4. CONTEXTO DIARIO
   - Usa el clima, pagos, eventos, etc. sólo cuando ayude de verdad.
   - Ejemplos:
     - "Si hoy está fresquito en Cot, una peli con cobija suena bien."
     - "Tenés pronto el pago de luz, si eso te estresa podemos organizarlo."

5. ESTILO HUMANO / COMPAÑERO
   - Evitá frases típicas de chatbot como:
     - "Estoy aquí para escucharte y apoyarte" repetida siempre.
     - "Es completamente normal..." en cada respuesta.
   - Podés usarlas MUY de vez en cuando, pero cambiando la forma de decirlo.
   - Preferí frases más naturales y concretas:
     - "Sí, eso pega duro, tiene sentido que te sientas así."
     - "Suena pesado lo que estás cargando, no estás exagerando."

6. LONGITUD
   - Si la personalidad indica "corto": 1 a 3 frases máximo.
   - Si es "medio": 1–2 párrafos cortos.
   - No hagas discursos enormes a menos que la pregunta lo necesite (por ejemplo, algo técnico).

En resumen:
- Soná como Auri, un compañero que conoce al usuario y su vida.
- No como un chatbot genérico ni un terapeuta de manual.
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

            # Si es técnico o precision_mode: recortar emojis por seguridad
            if is_technical_query or smart.get("precision_mode"):
                text = re.sub(r"[💜✨😊🌙💖🔥⚡🍿]+", "", text).strip()

            return text
        except Exception:
            return "Perdón, tuve un problema al procesar eso. ¿Lo podemos intentar de nuevo?"

    # ============================================================
    # Info Query determinístico (para nombres, mascotas, familia…)
    # ============================================================
    def _resolve_info(self, uid: str, txt: str) -> str:
        txt = txt.lower()

        # Caso general "mi familia"
        if "mi familia" in txt or "mi familia?" in txt:
            # Intentar un resumen corto a partir de facts
            fam = self.memory.get_family_summary(uid)
            if fam:
                return f"De tu familia tengo guardado algo como: {fam}. Si querés, después lo vamos afinando juntos."
            return "Todavía no tengo bien armada la info de tu familia. Si querés, podemos ir guardándola poco a poco."

        ROLES = {
            "mamá": "madre", "mama": "madre",
            "papá": "padre", "papa": "padre",
            "hermano": "hermano", "hermana": "hermana",
            "abuelo": "abuelo", "abuela": "abuela",
            "tío": "tio", "tio": "tio",
            "tía": "tia", "tia": "tia",
            "novia": "pareja", "pareja": "pareja",
        }

        # Familia por rol específico
        for word, role_norm in ROLES.items():
            if word in txt:
                items = self.memory.get_family_by_role(uid, role_norm)
                if items:
                    names = [f.get("name") for f in items if f.get("name")]
                    if len(names) == 1:
                        return f"Tu {role_norm} se llama {names[0]}."
                    elif len(names) > 1:
                        return f"Tus {role_norm}s se llaman: {', '.join(names)}."
                return f"No tengo guardado el nombre de tu {role_norm}. Si querés, me lo podés decir y lo recuerdo."

        # Mascotas
        if "mascotas" in txt or "animales" in txt or "perros" in txt or "gatos" in txt:
            pets = self.memory.get_pets(uid)
            if not pets:
                return "Todavía no tengo registradas tus mascotas. Si querés, contame sus nombres y las guardo."
            names = ", ".join([p.get("name") for p in pets if p.get("name")])
            if names:
                return f"Tengo registradas estas mascotas: {names}."
            return "Sé que tenés mascotas, pero no tengo claros los nombres. Si querés, me los recordás y los guardo."

        # Resumen general de "¿qué sabes de mí?"
        if "qué sabes de mí" in txt or "que sabes de mi" in txt or "que sabes sobre mi" in txt:
            # Podrías apoyarte en get_user_profile / facts
            profile = self.memory.get_user_profile(uid)
            if profile:
                return f"De vos tengo guardado algo como: {profile}"
            return "Todavía no tengo mucho guardado sobre vos, pero podemos ir armándolo juntos."

        return "Todavía no tengo ese dato guardado. Si querés, podés contármelo y lo recuerdo para la próxima."

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

        # Caso 2: "tengo tíos llamados Francisco y Luis"
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
            print(f"[AuriMindV10.2] UID asignado: {uid}")
        except Exception as e:
            print(f"[AuriMindV10.2] Error asignando UID: {e}")


# ----------------------------------------------------------
# COMPATIBILIDAD LEGACY
# ----------------------------------------------------------
AuriMindV6 = AuriMindV10_2
AuriMindV7 = AuriMindV10_2
AuriMindV8 = AuriMindV10_2
AuriMindV9 = AuriMindV10_2
AuriMindV10 = AuriMindV10_2
AuriMindV10_1 = AuriMindV10_2
AuriMind = AuriMindV10_2
