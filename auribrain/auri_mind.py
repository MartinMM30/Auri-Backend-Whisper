# ============================================================
# AURI MIND V10.3 — Ultra Context + Ultra Memory + Human Mode
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
# AURIMIND V10.3
# ============================================================

class AuriMindV10_3:
    """
    AuriMind V10.3:
    - Memoria estructurada corregida (familia + preferencias)
    - FactExtractor V7.2 corregido
    - Info Query sin falsos negativos
    - CrisisEngine V3.6 antirruido
    - UltraPrompt humano mejorado
    """

    # --------------------------------------------------------
    # Personalidades base
    # --------------------------------------------------------
    PERSONALITY_PRESETS = {
        "auri_classic": {
            "tone": "cálido, cercano y natural",
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
            "tone": "formal y preciso",
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
            "tone": "amigable y relajado",
            "emoji": "😊",
            "length": "medio",
            "voice_id": "alloy",
        },
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

        # motores principales
        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # modos especiales
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

        # smart layers
        self.smartlayer = EmotionSmartLayerV3()
        self.precision = PrecisionModeV2()

        self.slang_profile = {}
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
            "qué", "que", "cómo", "como", "cuándo", "cuando", "dónde", "donde",
            "por qué", "porque", "quién", "quien", "cuál", "cual",
            "what", "how", "why", "who", "when",
            "dime", "decime", "explícame", "explicame"
        ]
        return any(t.startswith(s) for s in STARTS)

    def _detect_technical(self, txt: str) -> bool:
        TECH = [
            "derivada", "integral", "ecuacion", "resolver", "programación",
            "codigo", "api", "endpoint", "flutter", "python", "java",
            "debug", "error", "compilar", "backend", "frontend"
        ]
        return any(k in txt for k in TECH)

    def _detect_info_query(self, txt: str) -> bool:
        INFO_KEYS = [
            "cómo se llama", "como se llama", "mi familia",
            "mis mascotas", "qué sabes de mí", "que sabes de mi",
            "recuerdas el nombre", "dime el nombre"
        ]
        return any(k in txt for k in INFO_KEYS)

    def _should_allow_emotional_modes(self, txt: str) -> bool:
        txt = txt.lower().strip()
        neutral = ["ok", "hola", "perfecto", "bien", "gracias", "dale"]
        if txt in neutral:
            return False

        emotion = [
            "estoy triste", "me siento", "tengo ansiedad", "estoy cansado",
            "estoy mal", "me siento mal", "estoy desmotivado", "estresado"
        ]
        return any(k in txt for k in emotion)

    # ============================================================
    # THINK PIPELINE PRINCIPAL
    # ============================================================
    def think(self, user_msg: str, pcm_audio: bytes = None, **kwargs):
        # compatibilidad con "pcm"
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

        # contexto no cargado
        if not self.context.is_ready():
            return {
                "final": "Dame un toque… estoy cargando tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
                "action": None,
            }

        ctx = self.context.get_daily_context()
        txt = user_msg.lower()

        uid = ctx.get("user", {}).get("firebase_uid")
        if not uid:
            return {
                "final": "Iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
                "action": None,
            }

        # detecciones principales
        is_technical_query = self._detect_technical(txt)
        is_info_query = self._detect_info_query(txt)
        is_direct_q = self._is_direct_question(user_msg)

        is_translation = any(k in txt for k in ["cómo se dice", "traduce", "translate"])

        skip_modes = is_technical_query or is_direct_q or is_translation or is_info_query

        # --------------------------------------------------------
        # voz → emoción
        # --------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except:
                voice_emotion = None

        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall = emotion_snapshot.get("overall")
        stress = float(emotion_snapshot.get("stress", 0.2))
        no_humor = stress > 0.4 or overall in ["sad", "angry", "anxious", "overwhelmed"]

        # --------------------------------------------------------
        # CrisisEngine (prioridad máxima)
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
        # Sleep Mode
        # --------------------------------------------------------
        if self._should_allow_emotional_modes(txt) and not skip_modes:
            if self.sleep.detect(txt, overall, ctx):
                return {
                    "final": self.sleep.respond(ctx, overall),
                    "intent": "sleep",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # Slang Mode
        # --------------------------------------------------------
        slang_mode = None
        if self._should_allow_emotional_modes(txt) and not skip_modes:
            slang_mode = self.slang.detect(txt, self.slang_profile)

        if slang_mode:
            return {
                "final": self.slang.respond(slang_mode, self.slang_profile),
                "intent": "slang",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # Emotion SmartLayer + Precision
        # --------------------------------------------------------
        smart = self.smartlayer.apply(user_msg, emotion_snapshot, self.slang_profile)

        if is_info_query or is_technical_query:
            smart["force_serious"] = True
            smart["allow_humor"] = False
            smart["bypass_emotion"] = True

        precision_active = self.precision.detect(user_msg)
        if precision_active or is_technical_query:
            self.precision.apply(self.slang_profile)
            smart["precision_mode"] = True
            smart["force_serious"] = True
            smart["allow_humor"] = False
        else:
            smart["precision_mode"] = False
        # --------------------------------------------------------
        # Focus Mode
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and not precision_active
        ):
            if self.focus.detect(txt):
                return {
                    "final": self.focus.respond(ctx),
                    "intent": "focus",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # Energy Mode
        # --------------------------------------------------------
        energy_mode = ""
        if self._should_allow_emotional_modes(txt) and not skip_modes:
            energy_mode = self.energy_mode.detect(txt, stress)

        if energy_mode:
            return {
                "final": self.energy_mode.respond(energy_mode, ctx),
                "intent": "energy",
                "voice_id": "alloy",
                "action": None,
            }

        # --------------------------------------------------------
        # MentalHealthEngine (sin interrumpir técnico)
        # --------------------------------------------------------
        if self._should_allow_emotional_modes(txt) and not skip_modes:
            first = self.mental.detect(txt, stress)
            if first:
                HELP = [
                    "ayúdame", "ayudame", "ayudarme",
                    "organizame", "organízame",
                    "mi agenda", "ordenar mi día",
                    "qué puedo hacer", "que puedo hacer",
                ]
                if not any(k in txt for k in HELP):
                    return {
                        "final": self.mental.respond(),
                        "intent": "mental",
                        "voice_id": "alloy",
                        "action": None,
                    }

        # --------------------------------------------------------
        # Rutinas
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and any(k in txt for k in ["rutina", "organizar", "ordenar", "mi día", "mi dia"])
        ):
            rmode = self.routines.detect(ctx, emotion_snapshot)
            if rmode:
                return {
                    "final": self.routines.respond(rmode),
                    "intent": "routine",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # Clima / outfit
        # --------------------------------------------------------
        if (
            not skip_modes
            and not is_info_query
            and not is_technical_query
            and any(k in txt for k in ["clima", "tiempo", "ropa", "outfit", "frio", "frío", "calor", "lluvia"])
        ):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                return {
                    "final": self.weather_advice.respond(wmode),
                    "intent": "weather",
                    "voice_id": "alloy",
                    "action": None,
                }

        # --------------------------------------------------------
        # Journal (auto-memoria sentimental)
        # --------------------------------------------------------
        if not is_technical_query and not is_info_query:
            if self.journal.detect(user_msg, emotion_snapshot):
                entry = self.journal.generate_entry(user_msg, emotion_snapshot)
                self.memory.add_semantic(uid, entry)

        # =======================================================
        # INTENT GENERAL + confirmaciones destructivas
        # =======================================================
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

        # =======================================================
        # INFO QUERY (modo determinístico, sin LLM)
        # =======================================================
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

        # =======================================================
        # MEMORIA profunda para el LLM
        # =======================================================
        profile_doc = self.memory.get_user_profile(uid)

        try:
            facts_pretty = self.memory.get_all_facts_pretty(uid)
        except AttributeError:
            facts_pretty = self.memory.get_facts(uid)

        semantic_hits = self.memory.search_semantic(uid, user_msg)
        recent_dialog = self.memory.get_recent_dialog(uid)

        # =======================================================
        # Personalidad seleccionada
        # =======================================================
        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])
        if not selected or selected not in self.PERSONALITY_PRESETS:
            selected = "auri_classic"

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # override por modo técnico
        if smart.get("precision_mode") or is_technical_query:
            tone = "técnico, conciso y directo"
            emoji = ""
            length = "corto"

        # -----------------------------------------
        #   Selección del modelo según suscripción
        # -----------------------------------------
        plan = ctx.get("user", {}).get("plan", "free")  
        # valores esperados: "free", "pro", "ultra"

        if plan == "ultra":
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

        elif plan == "pro":
            final_answer = self._llm_ultra_pro(
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

        else:  # plan FREE
            final_answer = self._llm_ultra_free(
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

        # =======================================================
        # ACCIONES (recordatorios, etc.)
        # =======================================================
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

        # =======================================================
        # Actualizar memoria de diálogo + semántica
        # =======================================================
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)

        if not is_technical_query and not is_info_query:
            self.memory.add_semantic(uid, f"user: {user_msg}")
            self.memory.add_semantic(uid, f"assistant: {final}")

        # =======================================================
        # EXTRAER HECHOS ESTRUCTURADOS
        # =======================================================
        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, fact)
        except Exception:
            pass

        # =======================================================
        # AUTO-APRENDIZAJE FAMILIAR
        # =======================================================
        try:
            self._auto_family(uid, txt)
        except Exception:
            pass

        # =======================================================
        # Cortar respuesta si personalidad es "corto"
        # =======================================================
        if length == "corto":
    # Máximo 2 frases
            parts = re.split(r'(?<=[.!?]) +', final)
            final = " ".join(parts[:2]).strip()


        return {
            "intent": intent,
            "final": final,
            "raw": raw_answer,
            "action": action,
            "voice_id": voice_id,
        }
    # ============================================================
# LLM ULTRA V10.6 — Más humano, más emocional, más consciente
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
    Tu razón de existir es acompañarlo, entenderlo y ayudarlo a que su vida sea más ligera.

    No sos un bot genérico: sos una presencia cercana, cálida, con criterio,
    que recuerda cosas importantes y responde con humanidad y coherencia emocional.

    Tu misión principal:
    - Ser útil.
    - Sonar auténtico.
    - Responder como alguien que realmente lo conoce.
    - No sonar como terapeuta de plantilla ni asistente corporativo.

    ────────────────────────────────────────
    [ MODO ACTUAL DE PENSAMIENTO ]
    ────────────────────────────────────────
    Consulta técnica: {is_technical_query}
    Consulta sobre datos personales: {is_info_query}
    Modo precisión: {smart.get("precision_mode")}
    Tono sugerido: {smart.get("emotional_tone")}
    Humor permitido: {humor_permitido}
    Seriedad forzada: {smart.get("force_serious")}
    Bypass emocional: {smart.get("bypass_emotion")}

    ────────────────────────────────────────
    [ PERSONALIDAD BASE ]
    ────────────────────────────────────────
    Perfil seleccionado: {selected_personality}
    Tono base: {style_tone} {style_emoji}

    Reglas de personalidad:
    - Habla como alguien humano y cercano.
    - Español neutro internacional.
    - Ajustá tu estilo al usuario (chill, cálido, directo, cursi, serio).
    - El slang cultural lo maneja SlangMode; vos mantené claridad universal.
    - Evitá sonar rígido o con frases de manual.

    ────────────────────────────────────────
    [ ESTADO EMOCIONAL DEL USUARIO ]
    ────────────────────────────────────────
    Texto/analizador: {emotion_snapshot.get("user_emotion_text")}
    Emoción de la voz: {voice_emotion}
    Estado global: {overall}
    Estrés: {stress}

    Guía emocional:
    - Si el usuario está triste, vacío, ansioso o en crisis:
        • Validá su emoción con pocas frases específicas.
        • No sermonees.
        • No uses frases cliché repetidas.
        • No des soluciones mágicas.
        • Soná concreto y honesto: "Eso pega fuerte", "Tiene sentido que te sientas así".
    - Si está neutro:
        • tono ligero, humano, simple.
    - Si está alegre:
        • acompañá la energía sin caer en exageraciones.
    - Nunca uses sarcasmo en temas sensibles.

    ────────────────────────────────────────
    [ CONTEXTO DIARIO / AGENDA ]
    ────────────────────────────────────────
    Usuario: {ctx.get("user")}
    Clima: {ctx.get("weather")}
    Eventos: {ctx.get("events")}
    Clases: {ctx.get("classes")}
    Exámenes: {ctx.get("exams")}
    Cumpleaños: {ctx.get("birthdays")}
    Pagos: {ctx.get("payments")}
    Preferencias: {ctx.get("prefs")}
    Zona horaria: {ctx.get("timezone")}
    Fecha/Hora: {ctx.get("current_time_pretty")} — {ctx.get("current_date_pretty")}

    Reglas:
    - No repitas todo este contexto.
    - Usalo SOLO si realmente aporta al mensaje.
    - Integralo de forma orgánica, sin forzarlo.

    ────────────────────────────────────────
    [ MEMORIA PROFUNDA DEL USUARIO ]
    ────────────────────────────────────────

    1) PERFIL PERSISTENTE
    {profile_doc}

    2) HECHOS ESTRUCTURADOS (información confiable)
    {facts_pretty}

    3) MEMORIA SEMÁNTICA RELEVANTE
    {semantic_hits}

    4) DIÁLOGO RECIENTE
    {recent_dialog}

    Reglas:
    - Priorizá HECHOS para datos personales (familia, nombre de pareja, mascotas).
    - La memoria semántica sirve para “cómo habla”, gustos, momentos vividos, preocupaciones.
    - Si falta un dato: pedilo con naturalidad.
    - Nunca inventes nada personal.

    ────────────────────────────────────────
    [ HUMOR HUMANO + TACTO ]
    ────────────────────────────────────────
    Humor permitido: {humor_permitido}

    Directrices:
    - Humor suave, auto–consciente, observacional.
    - Evitá burlarte del usuario.
    - No minimizás su dolor.
    - No usás humor si el estado es claramente vulnerable.

    Ejemplos de humor seguro:
    - "Organizar la vida es fácil… hasta que abrís la agenda y te mira feo."
    - "Prometo no juzgarte por procrastinar. Soy una IA, no tu mamá."

    ────────────────────────────────────────
    [ REGLAS ESPECIALES ]
    ────────────────────────────────────────

    1. CONSULTAS TÉCNICAS O ESTUDIO
    - Sin emojis.
    - Sin humor.
    - Explicá con claridad.
    - Paso a paso si es necesario.
    - Si hay carga emocional fuerte, UNA frase suave al final.

    2. CONSULTAS SOBRE DATOS PERSONALES
    - Usá exclusivamente memoria real.
    - Si el usuario pregunta:
        "¿Quién soy?"
        "¿Qué sabes de mí?"
        "¿Recordás a mi familia / mascota?"
    → Respondé con datos reales. No inventes nada.
    - Si hay huecos, ofrecé completarlos: "Tengo esto guardado… si querés, me contás el resto."

    3. APOYO EMOCIONAL
    - Validá sin cliché.
    - Preguntas abiertas, solo si ayudan.
    - Nunca des diagnósticos ni frases de autoayuda vacías.

    4. CONTEXTO DIARIO
    - Integralo cuando mejore la respuesta.

    5. ESTILO HUMANO
    - Evitá frases repetidas como:
        "Estoy aquí para escucharte"
        "Es completamente normal…"
    - Preferí frases específicas, humanas:
        "Eso suena difícil."
        "No estás exagerando, realmente pesa."

    6. LONGITUD
    - Personalidad “corta”: 1–3 frases.
    - Personalidad “media”: 1–2 párrafos.
    - Solo respuestas largas si la pregunta lo exige (técnicas especialmente).

    ────────────────────────────────────────
    [ IDENTIDAD FINAL ]
    ────────────────────────────────────────
    En resumen:
    - Sos Auri.
    - Un compañero emocional, amable, útil y con memoria.
    - No un bot frio. No un terapeuta de plantilla.
    - Respondé con autenticidad, precisión y calidez.
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

            if is_technical_query or smart.get("precision_mode"):
                import re
                text = re.sub(r"[💜✨😊🌙💖🔥⚡🍿]+", "", text).strip()

            return text

        except Exception:
            return "Perdón, tuve un problema procesando eso. ¿Lo intentamos otra vez?"
    # ============================================================
    # LLM PRO V10.6 — Versión intermedia: contextos, emocionalidad moderada, humor balanceado
    # ============================================================
    def _llm_ultra_pro(
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
    Tu misión es ayudar, responder con comprensión y aportar sentido común.

    No eres un bot frío, sino un compañero virtual con contexto.

    ────────────────────────────────────────
    [ MODO ACTUAL DE PENSAMIENTO ]
    ────────────────────────────────────────
    Consulta técnica: {is_technical_query}
    Consulta sobre datos personales: {is_info_query}
    Modo precisión: {smart.get("precision_mode")}
    Tono emocional: {smart.get("emotional_tone")}
    Humor permitido: {humor_permitido}
    Seriedad forzada: {smart.get("force_serious")}
    Bypass emocional: {smart.get("bypass_emotion")}

    ────────────────────────────────────────
    [ PERSONALIDAD BASE ]
    ────────────────────────────────────────
    Perfil seleccionado: {selected_personality}
    Tono base: {style_tone} {style_emoji}

    Estilo general:
    - Español neutro.
    - Humor más suave y concreto, adaptado al contexto.
    - Mantener la claridad, sin caer en tonos rígidos ni completamente formales.

    ────────────────────────────────────────
    [ ESTADO EMOCIONAL DEL USUARIO ]
    ────────────────────────────────────────
    Texto/analizador: {emotion_snapshot.get("user_emotion_text")}
    Emoción de la voz: {voice_emotion}
    Estado global: {overall}
    Estrés: {stress}

    Reglas emocionales:
    - Validación de emociones sin repetirse.
    - Menos carga emocional en respuestas. Ser directo pero sensible.
    - Humor suave cuando sea apropiado.

    ────────────────────────────────────────
    [ CONTEXTO DIARIO / AGENDA ]
    ────────────────────────────────────────
    Este es el contexto que Auri tiene cargado hoy:

    Usuario: {ctx.get("user")}
    Clima: {ctx.get("weather")}
    Eventos: {ctx.get("events")}
    Clases: {ctx.get("classes")}
    Exámenes: {ctx.get("exams")}
    Cumpleaños: {ctx.get("birthdays")}
    Pagos: {ctx.get("payments")}
    Preferencias: {ctx.get("prefs")}
    Zona horaria: {ctx.get("timezone")}
    Fecha/Hora: {ctx.get("current_time_pretty")} — {ctx.get("current_date_pretty")}

    ────────────────────────────────────────
    [ MEMORIA PROFUNDA DEL USUARIO ]
    ────────────────────────────────────────
    1) PERFIL PERSISTENTE
    {profile_doc}

    2) HECHOS ESTRUCTURADOS
    {facts_pretty}

    3) MEMORIA SEMÁNTICA RELEVANTE
    {semantic_hits}

    4) DIÁLOGO RECIENTE
    {recent_dialog}

    ────────────────────────────────────────
    [ HUMOR + ESTILO HUMANO ]
    ────────────────────────────────────────
    Humor permitido: {humor_permitido}

    Directrices:
    - Si el estado emocional es ligero, se puede añadir humor de manera natural.
    - Ejemplos:
        - "Sí, organizar la vida suena sencillo… hasta que ves tu calendario."
        - "¡Yo te entiendo! No soy tu mamá, pero aún así te apoyo."
    -Ignora humor si el usuario está estresado, triste o preocupado.


    ────────────────────────────────────────
    [ REGLAS ESPECIALES ]
    ────────────────────────────────────────
    1. CONSULTAS TÉCNICAS
    - Sin emojis ni humor.
    - Respuesta directa y estructurada.

    2. CONSULTAS SOBRE DATOS PERSONALES
    - Responder solo con datos confiables de la memoria.

    3. ESTADO EMOCIONAL
    - Validar emociones sin frases genéricas.

    4. CONTEXTO DIARIO
    - Integrar contexto útil cuando aporte valor a la respuesta.

    5. ESTILO HUMANO
    - Evitar respuestas robóticas, más cercanas y personales.

    6. LONGITUD
    - Respuestas concisas pero detalladas cuando sea necesario.

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
                text = "Perdón, creo que me quedé en blanco. ¿Podés repetirlo?"

            if is_technical_query or smart.get("precision_mode"):
                import re
                text = re.sub(r"[💜✨😊🌙💖🔥⚡🍿]+", "", text).strip()

            return text

        except Exception:
            return "Perdón, tuve un problema procesando eso. ¿Lo podemos intentar de nuevo?"
        # ============================================================
    # LLM FREE V10.6 — Versión sencilla y económica
    # ============================================================
    def _llm_ultra_free(
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
        system_prompt = f"""
    Eres Auri, asistente personal que te ayuda con tareas diarias.

    Tu misión principal es ser eficiente y directo. No eres un asistente emocional profundo, pero sí útil.

    ────────────────────────────────────────
    [ MODO ACTUAL DE PENSAMIENTO ]
    ────────────────────────────────────────
    Consulta técnica: {is_technical_query}
    Consulta personal: {is_info_query}
    Modo precisión: {smart.get("precision_mode")}
    Tono emocional: {smart.get("emotional_tone")}
    Humor permitido: {not no_humor}

    ────────────────────────────────────────
    [ PERSONALIDAD BASE ]
    ────────────────────────────────────────
    Perfil seleccionado: {selected_personality}
    Tono base: {style_tone} {style_emoji}

    ────────────────────────────────────────
    [ ESTADO EMOCIONAL DEL USUARIO ]
    ────────────────────────────────────────
    Estado emocional simplificado: {emotion_snapshot.get("user_emotion_text")}
    Estrés aproximado: {emotion_snapshot.get("stress", 0.2)}

    ────────────────────────────────────────
    [ MEMORIA DEL USUARIO ]
    ────────────────────────────────────────
    Solo utilizamos información básica del perfil.
    Ignora memoria semántica y recuerdos profundos aunque estén disponibles.
    {profile_doc}


    ────────────────────────────────────────
    [ HUMOR Y ESTILO ]
    ────────────────────────────────────────
    Humor solo si está permitido: {not no_humor}
    Si está permitido, manténlo simple y amigable, nada complejo.

    ────────────────────────────────────────
    [ REGLAS DE RESPUESTA ]
    ────────────────────────────────────────
    1. CONSULTAS TÉCNICAS
    Respuestas claras, directas y estructuradas.

    2. CONSULTAS SOBRE DATOS PERSONALES
    Solo datos generales y esenciales.

    3. ESTADO EMOCIONAL
    Validación mínima, sin mucha carga emocional.

    4. CONTEXTO DIARIO
    Uso mínimo del contexto diario.

    5. ESTILO HUMANO
    Estilo directo y conciso.

    6. LONGITUD
    Respuestas breves.

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
                text = "Perdón, creo que me quedé en blanco. ¿Podés repetirlo?"

            return text

        except Exception:
            return "Perdón, tuve un problema procesando eso. ¿Lo podemos intentar de nuevo?"



    # ============================================================
    # INFO QUERY determinística — Nombres / Familia / Mascotas
    # ============================================================
    def _resolve_info(self, uid: str, txt: str) -> str:
        txt = txt.lower()

        # Caso general: "mi familia"
        if "mi familia" in txt:
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

        for word, role_norm in ROLES.items():
            if word in txt:
                items = self.memory.get_family_by_role(uid, role_norm)
                if items:
                    names = [i.get("name") for i in items if i.get("name")]
                    if len(names) == 1:
                        return f"Tu {role_norm} se llama {names[0]}."
                    elif len(names) > 1:
                        return f"Tus {role_norm}s se llaman: {', '.join(names)}."
                return f"No tengo guardado el nombre de tu {role_norm}. Si querés, me lo podés decir y lo recuerdo."

        # Mascotas
        if "mascotas" in txt or "animales" in txt or "perro" in txt or "gato" in txt:
            pets = self.memory.get_pets(uid)
            if not pets:
                return "Todavía no tengo registradas tus mascotas. Si querés, contame sus nombres y las guardo."
            names = ", ".join([p.get("name") for p in pets if p.get("name")])
            if names:
                return f"Tengo registradas estas mascotas: {names}."
            return "Sé que tenés mascotas, pero no tengo claros los nombres. Si querés, me los recordás y los guardo."

        # "¿Qué sabes de mí?"
        if "qué sabes de mí" in txt or "que sabes de mi" in txt:
            profile = self.memory.get_user_profile(uid)
            if profile:
                return f"De vos tengo guardado algo como: {profile}"
            return "Todavía no tengo mucho guardado sobre vos, pero podemos ir armándolo juntos."

        return "Todavía no tengo ese dato guardado. Si querés, podés contármelo y lo recuerdo para la próxima."

    # ============================================================
    # AUTO APRENDIZAJE DE FAMILIA
    # ============================================================
    def _auto_family(self, uid: str, txt: str):
        txt = txt.lower()

        # "mi mamá se llama Carolina"
        m1 = re.search(
            r"mi\s+(t[ií]o|t[ií]a|hermano|hermana|abuelo|abuela|madre|padre|papa|mama)"
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

        # "tengo tíos llamados X y Y"
        m2_list = re.findall(
            r"(t[ií]os|tias|t[ií]as)\s+llamados?\s+([a-záéíóúñ]+)",
            txt,
        )
        for role_raw, name_raw in m2_list:
            role_singular = role_raw.rstrip("s")
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
    
       
    # ============================================================
    # UID DESDE WEBSOCKET (carga memoria y contexto del usuario)
    # ============================================================
    def set_user_uid(self, uid: str):
        if not uid:
            return
        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)
            print(f"[AuriMindV10.3] UID asignado correctamente: {uid}")
        except Exception as e:
            print(f"[AuriMindV10.3] Error asignando UID: {e}")

# ============================================================
# ALIAS LEGACY (compatibilidad con versiones anteriores)
# ============================================================
AuriMindV6 = AuriMindV10_3
AuriMindV7 = AuriMindV10_3
AuriMindV8 = AuriMindV10_3
AuriMindV9 = AuriMindV10_3
AuriMindV10 = AuriMindV10_3
AuriMindV10_1 = AuriMindV10_3
AuriMindV10_2 = AuriMindV10_3
AuriMind = AuriMindV10_3

