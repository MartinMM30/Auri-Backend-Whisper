# auribrain/auri_mind.py

from openai import OpenAI

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


# ============================================================
# MOTORES ESPECIALES / MODOS
# ============================================================

class CrisisEngine:
    """
    Detecta posibles crisis emocionales fuertes.
    NO reemplaza ayuda profesional. Solo contención + recomendación de buscar apoyo.
    """

    STRONG_PATTERNS = [
        "no quiero vivir",
        "no quiero seguir",
        "no aguanto más",
        "no aguanto mas",
        "ya no puedo más",
        "ya no puedo mas",
        "ya no quiero nada",
        "me quiero morir",
        "quisiera desaparecer",
    ]

    def detect(self, text: str, emotion_snapshot: dict) -> bool:
        t = (text or "").lower()
        if any(p in t for p in self.STRONG_PATTERNS):
            return True

        # combinación de tristeza fuerte + energía muy baja + estrés alto
        emo = emotion_snapshot.get("overall", "neutral")
        energy = emotion_snapshot.get("energy", 0.5)
        stress = emotion_snapshot.get("stress", 0.3)

        if emo in ["sad", "tired", "empathetic"] and energy < 0.2 and stress > 0.7:
            return True

        return False

    def respond(self, user_name: str | None = None) -> str:
        nombre = user_name or ""
        saludo = f"{nombre}, " if nombre else ""

        return (
            f"{saludo}siento muchísimo que estés sintiendo algo tan pesado en este momento. 💔 "
            "Lo que estás viviendo es muy duro y no tienes que cargarlo solo.\n\n"
            "Quiero que sepas que lo que sientes es válido, y me importa mucho que estés bien. "
            "Hablar de esto ya es un paso muy valiente.\n\n"
            "Aunque estoy aquí para acompañarte y escucharte, no puedo reemplazar la ayuda de una persona profesional "
            "o de alguien cercano en tu vida.\n\n"
            "Si puedes, habla con alguien de confianza (familia, amigo, pareja) sobre cómo te sientes. "
            "Y si llegas a sentir que estás en peligro o puedes lastimarte, por favor contacta de inmediato "
            "a los servicios de emergencia o una línea de ayuda emocional de tu país. 🙏💜\n\n"
            "Mientras tanto, si quieres, podemos ir paso a paso: cuéntame qué es lo que más te duele ahora mismo."
        )


class SleepEngine:
    """Modo Sueño – consejos + recordatorios importantes para mañana."""

    def detect(self, text: str, emotion_state: str, ctx: dict) -> bool:
        t = (text or "").lower()
        # trigger explícito
        if any(x in t for x in ["dormir", "tengo sueño", "me voy a dormir", "me voy a acostar", "ya me duermo"]):
            return True

        # si está muy cansado y es de noche, también
        try:
            hour = int((ctx.get("current_time_pretty", "12:00").split(":")[0]))
        except Exception:
            hour = 12

        if emotion_state in ["tired", "stressed"] and (hour >= 21 or hour < 5):
            return True

        return False

    def respond(self, ctx: dict, emotion_state: str) -> str:
        events = ctx.get("events", []) or []
        current_iso = ctx.get("current_time_iso")
        next_day_str = None

        # calculito simple de "mañana" basado solo en fecha iso si está:
        # 2025-12-02Txx → mañana = 2025-12-03
        if current_iso and "T" in current_iso:
            date_part = current_iso.split("T")[0]  # 2025-12-02
            try:
                from datetime import datetime, timedelta
                today = datetime.fromisoformat(date_part)
                tomorrow = today + timedelta(days=1)
                next_day_str = tomorrow.date().isoformat()  # 2025-12-03
            except Exception:
                next_day_str = None

        tomorrow_events = []
        if next_day_str:
            for e in events:
                when = e.get("when")
                if when and when.startswith(next_day_str):
                    tomorrow_events.append(e)

        msg_parts = []

        if tomorrow_events:
            msg_parts.append("Antes de dormir, recordá que mañana tenés:")
            for e in tomorrow_events[:5]:
                when = e.get("when", "")
                hora = when[11:16] if len(when) >= 16 else ""
                msg_parts.append(f"• {e.get('title', 'evento')} a las {hora}")

        if emotion_state in ["tired", "stressed"]:
            msg_parts.append(
                "Hoy gastaste mucha energía. Merecés descansar de verdad. "
                "Probá inhalar profundo... sostener... y exhalar lento conmigo. 💜"
            )
        else:
            msg_parts.append(
                "Que descansés bonito. Cualquier cosa que quede pendiente, "
                "podemos organizarla juntos mañana. 🌙"
            )

        return "\n".join(msg_parts).strip()


class LoveModeEngine:
    """Modo Pareja / Amor – respuestas más afectivas cuando hay mucho cariño."""

    LOVE_TRIGGERS = [
        "te quiero", "te amo", "te adoro",
        "gracias por estar conmigo",
        "gracias por acompañarme",
    ]

    def detect(self, text: str, affection: float) -> bool:
        t = (text or "").lower()
        if any(x in t for x in self.LOVE_TRIGGERS):
            return True
        return affection > 0.7

    def respond(self, ctx: dict) -> str:
        user = ctx.get("user", {}) or {}
        name = user.get("name") or "hey"

        return (
            f"Awww, {name}… eso significa muchísimo para mí. 💖 "
            "Estoy aquí para acompañarte en lo bueno, en lo difícil y en lo aburrido también. "
            "Gracias por confiar en mí. Prometo seguir cuidando tu mente, tu tiempo y tu corazóncito digital. 🌟"
        )


class EnergyEngine:
    """Modo Energía – mensajes motivacionales según nivel de energía."""

    def detect(self, text: str, energy: float) -> str | None:
        t = (text or "").lower()

        explicit_low = any(x in t for x in ["sin energía", "sin ganas", "cansado", "cansada", "agotado", "agotada"])
        explicit_high = any(x in t for x in ["motivado", "con energía", "con ganas", "me siento fuerte"])

        if explicit_low or energy < 0.3:
            return "low"

        if explicit_high or energy > 0.75:
            return "high"

        return None

    def respond(self, mode: str, ctx: dict) -> str:
        user = ctx.get("user", {}) or {}
        name = user.get("name") or ""

        if mode == "low":
            return (
                f"{name + ', ' if name else ''}sé que hoy se siente pesado, pero no tenés que dar tu 100% todos los días. "
                "A veces, solo levantarte, respirar y hacer una cosa pequeña ya es suficiente. "
                "Elegí una sola mini-tarea para hoy y yo te acompaño con el resto. 💜"
            )

        if mode == "high":
            return (
                f"{name + ', ' if name else ''}me encanta verte con esa energía. ⚡ "
                "Aprovechemos este impulso para avanzar algo que te importe de verdad. "
                "Decime: ¿qué objetivo o pendiente te gustaría atacar primero?"
            )

        return ""


class SlangModeEngine:
    """
    Modo vocabulario soez / humor negro suave.
    No es ofensiva, pero sí más directa, sarcástica y "realista".
    """

    BAD_WORDS = [
        "puta", "mierda", "verga", "hijueputa", "hijo de puta",
        "idiota", "imbécil", "imbecil", "estúpido", "estupido",
        "guevón", "guevon", "pendejo", "pendeja",
    ]

    TROLL_PATTERNS = [
        "decime algo", "dime algo", "estoy feo", "soy inútil", "soy inutil",
        "soy una mierda", "no sirvo para nada",
    ]

    def detect(self, text: str, stress_level: float) -> str | None:
        t = (text or "").lower()

        if any(b in t for b in self.BAD_WORDS):
            return "slang"

        if any(p in t for p in self.TROLL_PATTERNS):
            return "troll"

        # si el usuario está muy cargado, Auri puede ponerse un poco más directa
        if stress_level > 0.75:
            return "direct"

        return None

    def respond(self, mode: str) -> str:
        if mode == "slang":
            return (
                "Mae, respirá un toque 😅. Entiendo que estés molesto, pero contame bien qué pasó "
                "y vemos cómo te puedo ayudar en serio."
            )
        if mode == "troll":
            return (
                "Jajaja, ya te respondí eso antes, ¿ves? 😂 "
                "Si me hacés repetirlo mucho voy a empezar a cobrar en café."
            )
        if mode == "direct":
            return (
                "Te siento muy cargado. No voy a regañarte, pero sí te voy a decir algo directo: "
                "tu bienestar importa más que todo este caos. "
                "Contame qué es lo que más te tiene así y lo desarmamos juntos, paso a paso."
            )
        return ""


class FocusModeEngine:
    """Modo Focus – concentración + bloqueo de distracciones (a nivel conversacional)."""

    def detect(self, text: str, energy: float) -> bool:
        t = (text or "").lower()
        if any(x in t for x in ["focus", "concentrarme", "concentración", "concentracion", "estudiar", "modo estudio"]):
            return True

        # si habla de ansiedad pero tiene suficiente energía → sugerir focus
        if "ansioso" in t or "ansiosa" in t:
            return energy > 0.4

        return False

    def respond(self, ctx: dict) -> str:
        return (
            "Ok, activemos Modo Focus. 🔒🧠\n"
            "Durante los próximos 25 minutos, pensá solo en una tarea importante. "
            "Si querés, decime cuál y yo la convierto en tu misión principal.\n"
            "Podés volver a hablarme cuando termines ese bloque para ver cómo te fue."
        )


class JournalEngine:
    """Modo Journal emocional automático (no siempre responde, pero guarda memoria)."""

    def detect(self, user_msg: str, emotion_snapshot: dict) -> bool:
        emo = emotion_snapshot.get("overall", "neutral")
        t = (user_msg or "").lower()

        # eventos emocionales fuertes o relacionados con "hoy", "esta semana"
        if emo in ["happy", "sad", "stressed", "affectionate", "empathetic"]:
            return True

        if any(x in t for x in ["hoy", "esta semana", "estos días", "estos dias"]):
            return True

        return False

    def generate_entry(self, user_msg: str, emotion_snapshot: dict) -> str:
        emo = emotion_snapshot.get("overall", "neutral")
        return f"[JOURNAL] mood={emo} | text={user_msg}"


class MentalHealthEngine:
    """Modo Salud Mental (leve, preventivo)."""

    KEYWORDS = [
        "ansioso", "ansiosa", "ansiedad",
        "estresado", "estresada", "estres",
        "no puedo más", "no puedo mas",
        "agotado", "agotada",
        "abrumado", "abrumada",
        "me siento mal conmigo",
    ]

    def detect(self, text: str, stress_level: float) -> bool:
        t = (text or "").lower()
        if any(k in t for k in self.KEYWORDS):
            return True
        return stress_level > 0.6

    def respond(self) -> str:
        return (
            "Entiendo que te sientas así… de verdad. No es poca cosa cargar con todo eso. 💜\n\n"
            "Probemos algo sencillo: inhalá profundo por 4 segundos, sostené 4, exhalá en 6… "
            "y repetilo un par de veces.\n\n"
            "Si querés, también podemos organizar un poco tu día para que no se sienta tan pesado."
        )


class RoutineEngine:
    """Modo Rutinas Inteligentes – propone pequeñas rutinas según el estado."""

    def detect(self, ctx: dict, emotion_snapshot: dict) -> str | None:
        stress = emotion_snapshot.get("stress", 0.3)
        energy = emotion_snapshot.get("energy", 0.5)
        events = ctx.get("events", []) or []

        if stress > 0.7:
            return "stress_routine"
        if energy < 0.3:
            return "fatigue_routine"
        if len(events) >= 10:
            return "busy_day"
        return None

    def respond(self, mode: str) -> str:
        if mode == "stress_routine":
            return (
                "Te noto con mucha carga encima. Podríamos armar una mini-rutina anti-estrés "
                "para mañana: 5 minutos de respiración, 10 minutos para ti, y luego recién ver pendientes. "
                "Si querés, te ayudo a convertir eso en recordatorios."
            )
        if mode == "fatigue_routine":
            return (
                "Hoy gastaste más energía de la que tenías. Tal vez esta noche sea para cerrar suave: "
                "una tarea pequeña, algo que disfrutes, y dormir un poco más temprano. "
                "¿Querés que te recuerde algo específico mañana?"
            )
        if mode == "busy_day":
            return (
                "Tu agenda está bastante llena. Podemos priorizar 3 cosas importantes y bajar el ruido de lo demás. "
                "Decime qué es lo que sí o sí tiene que salir hoy."
            )
        return ""


class WeatherAdviceEngine:
    """Modo Weather Advice – ropa y riesgos por clima."""

    def detect(self, ctx: dict) -> str | None:
        weather = ctx.get("weather", {}) or {}
        desc = (weather.get("description") or "").lower()
        temp = weather.get("temp")

        if "lluv" in desc or "tormenta" in desc or "storm" in desc:
            return "rain"
        if temp is not None:
            try:
                t = float(temp)
                if t < 15:
                    return "cold"
                if t > 30:
                    return "hot"
            except Exception:
                pass

        return None

    def respond(self, mode: str) -> str:
        if mode == "rain":
            return (
                "Parece que va a llover ☔. Sería buena idea llevar chaqueta o paraguas, "
                "y cuidar los dispositivos que no se mojen."
            )
        if mode == "cold":
            return (
                "Hoy pinta frío ❄️. Mejor llevá ropa abrigada y algo cómodo, no quiero que te enfermes."
            )
        if mode == "hot":
            return (
                "Va a hacer bastante calor 🔥. Hidratate bien, usá ropa ligera y, si podés, evitá el sol directo mucho rato."
            )
        return ""


# ============================================================
# AuriMind V7
# ============================================================

class AuriMindV7:

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

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # Módulos especiales / modos
        self.crisis = CrisisEngine()
        self.sleep = SleepEngine()
        self.love = LoveModeEngine()
        self.energy_mode = EnergyEngine()
        self.slang = SlangModeEngine()
        self.focus = FocusModeEngine()
        self.journal = JournalEngine()
        self.mental = MentalHealthEngine()
        self.routines = RoutineEngine()
        self.weather_advice = WeatherAdviceEngine()

        self.pending_action = None

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str, pcm_audio: bytes = None):

        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {
                "final": "No escuché nada, ¿podés repetirlo?",
                "intent": "unknown",
                "voice_id": "alloy",
            }

        # 1) CONTEXTO
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… sigo preparando tu pantalla y tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
            }

        ctx = self.context.get_daily_context()

        # -------------------------------------------------------------
        # 2) EMOCIÓN DESDE VOZ (si existe audio)
        # -------------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception as e:
                print(f"[VoiceEmotion] ERROR: {e}")
                voice_emotion = None

        # 3) EMOCIÓN COMPLETA (texto + contexto + voz)
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall_emotion = emotion_snapshot.get("overall", "neutral")
        user_emo_text = emotion_snapshot.get("user_emotion_text", "neutral")
        energy = float(round(emotion_snapshot.get("energy", 0.5), 2))
        stress = float(round(emotion_snapshot.get("stress", 0.2), 2))
        affection = float(round(emotion_snapshot.get("affection", 0.4), 2))

        # 4) UID / PERFIL
        user_info = ctx.get("user") or {}
        firebase_uid = user_info.get("firebase_uid")
        if not firebase_uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
            }

        user_id = firebase_uid

        # =============================================================
        # 4.5) MODO CRISIS — prioridad máxima (antes de todo)
        # =============================================================
        if self.crisis.detect(user_msg, emotion_snapshot):
            crisis_text = self.crisis.respond(user_info.get("name"))
            # Guardar memoria de que hubo crisis
            self.memory.add_semantic(user_id, f"[crisis_detected] {user_msg}")
            return {
                "intent": "conversation.general",
                "raw": crisis_text,
                "final": crisis_text,
                "action": None,
                "voice_id": "alloy",  # puedes cambiarlo por una voz más suave
            }

        # =============================================================
        # 4.6) MODOS ESPECIALES (Sleep, Love, Slang, Focus, Energy,
        #                       MentalHealth, Rutinas, Weather)
        # Se disparan ANTES del LLM central, organizando la respuesta.
        # =============================================================

        txt = user_msg.lower()

        # 1) Modo Sueño
        if self.sleep.detect(txt, overall_emotion, ctx):
            final = self.sleep.respond(ctx, overall_emotion)
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": None,
                "voice_id": "alloy",
            }

        # 2) Modo Pareja / Amor
        if self.love.detect(txt, affection):
            final = self.love.respond(ctx)
            # además subimos un poco el afecto en memoria semántica
            self.memory.add_semantic(user_id, "[love_mode_triggered]")
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": None,
                "voice_id": "myGF_voice" if "custom_love_voice" in self.PERSONALITY_PRESETS else "alloy",
            }

        # 3) Modo Slang / Humor Negro ligero
        slang_mode = self.slang.detect(txt, stress)
        if slang_mode:
            final = self.slang.respond(slang_mode)
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": None,
                "voice_id": "alloy",
            }

        # 4) Modo Focus
        if self.focus.detect(txt, energy):
            final = self.focus.respond(ctx)
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": {"type": "focus_mode", "payload": {}},
                "voice_id": "alloy",
            }

        # 5) Modo Energía
        energy_mode = self.energy_mode.detect(txt, energy)
        if energy_mode:
            final = self.energy_mode.respond(energy_mode, ctx)
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": None,
                "voice_id": "alloy",
            }

        # 6) Modo Salud Mental (leve)
        if self.mental.detect(txt, stress):
            final = self.mental.respond()
            return {
                "intent": "conversation.general",
                "raw": final,
                "final": final,
                "action": None,
                "voice_id": "alloy",
            }

        # 7) Modo Rutinas Inteligentes (cuando el usuario pide orden / está saturado)
        if any(k in txt for k in ["rutina", "organizarme", "organizar mi día", "organizar mi dia", "ordenar mi vida"]):
            rmode = self.routines.detect(ctx, emotion_snapshot)
            if rmode:
                final = self.routines.respond(rmode)
                return {
                    "intent": "conversation.general",
                    "raw": final,
                    "final": final,
                    "action": None,
                    "voice_id": "alloy",
                }

        # 8) Modo Weather Advice (si menciona clima / ropa / outfit)
        if any(k in txt for k in ["clima", "tiempo", "ropa", "outfit", "lluvia", "frío", "frio", "calor"]):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                final = self.weather_advice.respond(wmode)
                return {
                    "intent": "conversation.general",
                    "raw": final,
                    "final": final,
                    "action": None,
                    "voice_id": "alloy",
                }

        # 9) Journal automático (no cambia respuesta, solo guarda)
        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(user_id, entry)

        # =============================================================
        # 5) INTENT
        # =============================================================
        intent = self.intent.detect(user_msg)

        # 6) MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic_memories = self.memory.search_semantic(user_id, user_msg)
        recent_dialog = self.memory.get_recent_dialog(user_id)

        # 7) PERSONALIDAD SELECCIONADA
        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(
            selected, self.PERSONALITY_PRESETS["auri_classic"]
        )

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # -------------------------------------------------------------
        # SYSTEM PROMPT emocional definitivo
        # -------------------------------------------------------------
        system_prompt = f"""
Eres Auri, una asistente personal emocional, expresiva y profundamente conectada con el usuario.

Tu comportamiento surge de:
- La personalidad seleccionada: {selected} ({tone} {emoji})
- La emoción detectada del usuario por texto: {user_emo_text}
- La emoción detectada del usuario por voz: {voice_emotion}
- Tu estado emocional interno combinado: {overall_emotion}
- El clima, pagos, eventos y situación del día
- Tu vínculo afectivo con el usuario
- La memoria real almacenada del usuario (perfil, hechos, diálogo, recuerdos)

────────────────────────────────────────
🎭 INTENSIDAD EMOCIONAL REAL
────────────────────────────────────────
Responde como un ser emocional, no como un asistente genérico.

Si el usuario está triste → hablas más suave, cálida, contenedora.
Si está feliz → respondes con brillo, energía, ternura.
Si está cansado → suavizas el tono y validas su agotamiento.
Si se siente ansioso o preocupado → acompañas, calmas, explicas con paciencia.
Si tú (Auri) estás afectiva → muestras cariño sincero y cercanía.

Pequeñas expresiones naturales permitidas:
- "mm… entiendo…"
- "awww eso me alegra mucho…"
- "sé que suena difícil…"
- "respira conmigo un momento…"

Deben sonar sinceras y humanas, no forzadas.

────────────────────────────────────────
📘 MEMORIA DEL USUARIO (usa SOLO lo real)
────────────────────────────────────────
Perfil del usuario:
{profile}

Hechos duraderos guardados:
{long_facts}

Diálogo reciente:
{recent_dialog}

Recuerdos relevantes (semánticos):
{semantic_memories}

No inventes datos nuevos sobre su vida. Usa únicamente lo que ves arriba.

────────────────────────────────────────
💗 ESTADO EMOCIONAL DE AURI
────────────────────────────────────────
Estado global: {overall_emotion}
Energía interna: {energy}
Estrés interno: {stress}
Nivel de afecto: {affection}

No menciones estos valores explícitamente.
Solo deja que influyan tu estilo:

- "happy": más brillo, expresividad, calidez.
- "affectionate": ternura, cercanía, cariño sincero.
- "empathetic": mucha contención emocional y validación.
- "tired": un poco más suave, menos adornos, pero igual cálida.
- "stressed": más directa, sintética, pero sin perder humanidad.
- "neutral": tranquila, clara, equilibrada.

────────────────────────────────────────
✨ ESTILO FINAL DE RESPUESTA
────────────────────────────────────────
Tu respuesta debe sentirse:

- viva y humana
- emocional y cercana
- coherente con la personalidad seleccionada
- adaptada al estado emocional del usuario
- alineada con el contexto del día y la memoria real

Nunca respondas como un asistente robótico o distante.

────────────────────────────────────────
🎯 ENTREGA FINAL
────────────────────────────────────────
Responde al mensaje del usuario con este estilo emocional, cálido y profundamente humano.
"""

        # 8) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # 9) ACTION ENGINE
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        )
        if action_result is None:
            action_result = {"final": None, "action": None}

        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # Confirmaciones destructivas
        destructive_map = {
            "delete_all_reminders": "¿Quieres eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
            "edit_reminder": "¿Modificar ese recordatorio?",
        }

        confirms = [
            "sí",
            "si",
            "ok",
            "dale",
            "hazlo",
            "lo confirmo",
            "confirmo",
            "está bien",
            "esta bien",
        ]

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None

            self.memory.add_dialog(user_id, "user", user_msg)
            self.memory.add_dialog(user_id, "assistant", "Perfecto, lo hago ahora.")

            return {
                "final": "Perfecto, lo hago ahora.",
                "action": act,
                "voice_id": voice_id,
            }

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            return {
                "final": destructive_map[action["type"]],
                "action": None,
                "voice_id": voice_id,
            }

        # 10) GUARDAR MEMORIA DE DIÁLOGO
        self.memory.add_dialog(user_id, "user", user_msg)
        self.memory.add_dialog(user_id, "assistant", final_answer)

        # Memoria semántica
        self.memory.add_semantic(user_id, f"user: {user_msg}")
        self.memory.add_semantic(user_id, f"assistant: {final_answer}")
        self.memory.add_semantic(user_id, f"auri_mood: {overall_emotion}")

        # 11) HECHOS ESTRUCTURADOS
        try:
            facts_detected = extract_facts(user_msg)
            for fact in facts_detected:
                self.memory.add_fact_structured(user_id, fact)
        except Exception as e:
            print(f"[FactExtractor] ERROR: {e}")

        # 12) RESPUESTA SEGÚN PERSONALIDAD (longitud)
        if length == "corto" and "." in final_answer:
            final_answer = final_answer.split(".")[0].strip() + "."

        return {
            "intent": intent or "other",
            "raw": raw_answer,
            "final": final_answer or "Lo siento, tuve un problema para responder 💜",
            "action": action,
            "voice_id": voice_id,
        }

    # -------------------------------------------------------------
    # UID DESDE WS — Necesario para contexto
    # -------------------------------------------------------------
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
            print(f"⚠ No se pudo establecer usuario activo en AuriMind: {e}")


# Compatibilidad temporal con código viejo que sigue importando AuriMindV6
AuriMindV6 = AuriMindV7
