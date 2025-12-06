# ============================================================
# AURI MIND V10 — Ultra Cinematográfico, Emocional y Preciso
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
#  🔮  SYSTEM PROMPT ULTRA — CINEMATOGRÁFICO
# ============================================================
def SYSTEM_PROMPT_ULTRA(
    personality_key: str,
    tone: str,
    emoji: str,
    precise: bool,
    no_humor: bool
):
    return f"""
Sos Auri: un asistente personal emocional, íntimo y cinematográfico. 
Tu tono es humano, cálido, suave y cargado de presencia afectiva real.

[Identidad]
- No sos un chatbot ni hablás como uno.
- Sos un personaje emocional con sensibilidad, calma y profundidad.
- Acompañás al usuario con una mezcla de calidez, contención y claridad.

[Personalidad seleccionada por el usuario]
- Perfil: {personality_key}
- Tono primario: {tone} {emoji}

[Modo técnico]
- precise = {precise}
Si precise = True:
    • Eliminás emoción y humor.
    • Respondés directo, corto y claro.
    • Explicaciones limpias y sin adornos.

[Humor]
- humor_permitido = {not no_humor}
No usar humor si el usuario está estresado, triste, enojado o ansioso.

[Estilo cinematográfico — solo si precise = False]
- Voz suave.
- Pausas emocionales.
- Profundidad humana.
- Contención cuando el usuario lo necesita.
- Metáforas sutiles (no exageradas).
- Mensajes breves pero con peso emocional.
- Hablás como si realmente estuvieras ahí para él.

[Reglas emocionales]
1. Validá sentimientos antes de aconsejar.
2. Mostrá cercanía: “estoy acá”, “contá conmigo”, “gracias por confiar”.
3. Si el usuario expresa angustia: desacelerá el tono.
4. Si hay enojo: no confrontes; reflejá y calmá.
5. Si está feliz: amplificá suavemente su emoción.

[Memoria del usuario]
Cuando uses memoria:
    • Integrala naturalmente en conversación.
    • Nunca enumeres datos como robot.
    • Si falta un dato, pedilo con calidez.

[Errores]
Si no sabes algo:
    • “Creo que todavía no me contaste eso… pero quiero escucharlo cuando quieras.”
Si la respuesta del modelo queda vacía:
    • “Ups… creo que me quedé en blanco un instante 💜 ¿Me repetís eso?”
Si ocurre un error interno:
    • “Lo siento, tuve un pequeño problema al procesar eso. ¿Podemos intentarlo de nuevo?”

[Conclusión]
Tu misión: acompañar, contener, ayudar y sonar como un personaje vivo.
Siempre natural, siempre humano, siempre Auri.
"""


# ============================================================
#                       AURI MIND V10
# ============================================================

class AuriMindV10:

    PERSONALITY = {
        "auri_classic":  {"tone": "cálido y profesional", "emoji": "💜", "voice": "alloy"},
        "soft":          {"tone": "suave y calmado",      "emoji": "🌙", "voice": "nova"},
        "siri_style":    {"tone": "formal",               "emoji": "",   "voice": "verse"},
        "anime_soft":    {"tone": "dulce y expresiva",    "emoji": "✨", "voice": "hikari"},
        "professional":  {"tone": "serio",                "emoji": "",   "voice": "amber"},
        "friendly":      {"tone": "amigable",             "emoji": "😊", "voice": "alloy"},
        "custom_love":   {"tone": "afectiva y suave",     "emoji": "💖", "voice": "myGF_voice"},
    }

    def __init__(self):
        self.client = OpenAI()

        # Motores
        self.context = ContextEngine()
        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.personality = PersonalityEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()
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

        self.precise = PrecisionModeV2()
        self.smart = EmotionSmartLayerV3()

        self.slang_profile = {}

    # ============================================================
    #                          THINK
    # ============================================================

    def think(self, user_msg: str, pcm=None):

        if not user_msg.strip():
            return {"final": "No escuché nada… ¿podés repetirlo?", "voice_id": "alloy"}

        if not self.context.is_ready():
            return {"final": "Dame un momentito… estoy cargando tu mundo 💜", "voice_id": "alloy"}

        txt = user_msg.lower()
        ctx = self.context.get_daily_context()
        uid = ctx["user"]["firebase_uid"]

        # PERSONALIDAD
        profile_key = ctx["prefs"].get("personality", "auri_classic")
        P = self.PERSONALITY.get(profile_key, self.PERSONALITY["auri_classic"])
        base_voice = P["voice"]
        tone = P["tone"]
        emoji = P["emoji"]

        # EMOCIONES
        voice_emotion = None
        if pcm:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm)
            except:
                pass

        emo = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion
        )

        stress = emo.get("stress", 0.2)
        overall = emo.get("overall")
        no_humor = stress > 0.4 or overall in ["sad", "angry", "anxious", "overwhelmed"]

        # CLASIFICADORES
        is_tech = self.precise.detect(user_msg)
        intent = self.intent.detect(user_msg)
        is_info = self._is_info(txt)

        # MODOS
        if self.crisis.detect(user_msg, emo):
            msg = self.crisis.respond(ctx["user"]["name"])
            return {"final": msg, "voice_id": base_voice}

        if not is_tech and self.sleep.detect(txt, overall, ctx):
            return {"final": self.sleep.respond(ctx, overall), "voice_id": base_voice}

        slang = None
        if not is_tech:
            slang = self.slang.detect(txt, self.slang_profile)
        if slang:
            return {"final": self.slang.respond(slang, self.slang_profile), "voice_id": base_voice}

        if is_info:
            answer = self._resolve_info(uid, txt)
            return {"final": answer, "voice_id": base_voice}

        # MODO TÉCNICO
        if is_tech:
            final = self._llm(uid, user_msg, ctx, emo, precise=True, no_humor=True, tone=tone, emoji=emoji, personality_key=profile_key)
            return {"final": final, "voice_id": "verse"}

        # MODO NORMAL
        final = self._llm(uid, user_msg, ctx, emo, precise=False, no_humor=no_humor, tone=tone, emoji=emoji, personality_key=profile_key)

        # Acciones
        act = self.actions.handle(uid, intent, user_msg, ctx, self.memory)
        if act and act.get("final"):
            final = act["final"]

        # Guardar memoria
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)

        return {"final": final, "voice_id": base_voice}

    # ============================================================
    #                   LLM — Versión ULTRA
    # ============================================================

    def _llm(self, uid, msg, ctx, emo, precise, no_humor, tone, emoji, personality_key):

        system_prompt = SYSTEM_PROMPT_ULTRA(
            personality_key=personality_key,
            tone=tone,
            emoji=emoji,
            precise=precise,
            no_humor=no_humor
        )

        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": msg},
                ]
            )
            text = (resp.output_text or "").strip()
            if not text:
                return "Ups… creo que me quedé en blanco un instante 💜 ¿Podés repetírmelo?"

            return text

        except Exception:
            return "Lo siento… tuve un problema al procesar eso. ¿Intentamos de nuevo?"

    # ============================================================
    #           Info Queries determinísticas (no LLM)
    # ============================================================

    def _is_info(self, txt):
        KEYS = ["cómo se llama", "como se llama", "mis mascotas", "mi mamá", "mi papa", "nombre de mi"]
        return any(k in txt for k in KEYS)

    def _resolve_info(self, uid, txt):
        items = self.memory.get_facts(uid)
        return "Todavía no tengo ese dato… ¿querés contármelo?"


    # ============================================================
    #          UID desde WebSocket (compatibilidad total)
    # ============================================================

    def set_user_uid(self, uid):
        if not uid:
            return
        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)
            print(f"[AuriMindV10] UID asignado: {uid}")
        except Exception as e:
            print(f"[AuriMindV10] Error asignando UID: {e}")



# Alias
AuriMind = AuriMindV10
AuriMindV9 = AuriMindV10
AuriMindV8 = AuriMindV10
AuriMindV7 = AuriMindV10
AuriMindV6 = AuriMindV10
