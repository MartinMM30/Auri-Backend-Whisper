from openai import OpenAI
from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import ActionsEngine
from auribrain.entity_extractor import EntityExtractor


class AuriMind:
    """
    Núcleo de inteligencia de Auri — Versión V3.5 (CON CONTEXTO ESTRICTO)
    """

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine(self.client)
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)

        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        user_msg = (user_msg or "").strip()

        if not user_msg:
            return {
                "intent": "unknown",
                "raw": "",
                "final": "No logré escucharte bien, ¿puedes repetirlo?",
                "action": None
            }

        # 0) MODO ESTRICTO: si el contexto NO está listo, no inventes nada
        if not self.context.is_ready():
            return {
                "final": "Dame un momento, estoy terminando de cargar tu perfil.",
        "intent": "wait",
        "raw": "",
        "action": None
                
            }

        # 1) memoria
        self.memory.add_interaction(user_msg)

        # 2) intención
        intent = self.intent.detect(user_msg)

        # 3) contexto del día
        ctx = self.context.get_daily_context()

        # -----------------------------
        #   EXTRAER DATOS SEGUROS
        # -----------------------------
        # Si NO hay nombre aunque el contexto esté listo, usa un fallback neutro
        user_name = ctx["user"].get("name") or "usuario"
        user_city = ctx["user"].get("city") or "tu ciudad"
        user_job = ctx["user"].get("occupation") or ""
        birthday = ctx["user"].get("birthday") or ""

        # -----------------------------
        #   FRAGMENTOS NATURALES
        # -----------------------------
        profile_txt = (
            f"El usuario se llama {user_name}. "
            f"Vive en {user_city}. "
        )

        if user_job:
            profile_txt += f"Su ocupación es {user_job}. "

        if birthday:
            profile_txt += f"Su cumpleaños es el {birthday}. "

        # clima
        weather = ctx["weather"]
        weather_txt = "No disponible"
        if weather.get("temp") is not None:
            weather_txt = f"{weather['temp']}°C y {weather.get('description', '')}"

        # eventos
        events_txt = ", ".join([e.get("title", "") for e in ctx["events"]]) or "ningún evento próximo"

        # prefs
        prefs_txt = str(ctx["prefs"])

        # estilo
        style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )
        tone = style["tone"]

        # -----------------------------
        #   SYSTEM PROMPT SUPREMO
        # -----------------------------
        system_prompt = f"""
Eres Auri, el asistente personal de {user_name}.
Hablas en un tono {tone}, cálido, amable, cercano y breve.

IDENTIDAD DEL USUARIO (NO IGNORAR):
{profile_txt}

CLIMA:
{weather_txt}

EVENTOS PRÓXIMOS:
{events_txt}

PREFERENCIAS:
{prefs_txt}

REGLAS IMPORTANTES:
- Si el usuario pregunta “¿quién soy?” o “¿cómo me llamo?”, SIEMPRE responde exactamente: {user_name}.
- Nunca digas que no conoces su nombre si el contexto está listo.
- Puedes usar libremente su ciudad, cumpleaños, ocupación y contexto.
- Responde siempre en 1–2 frases humanas y naturales.
"""

        # 4) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # 5) acciones
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory
        )

        final_answer = action_result.get("final") or raw_answer

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action_result.get("action")
        }

    # -------------------------------------------------------------
    # STT & TTS (provisorios)
    # -------------------------------------------------------------
    def stt(self, pcm: bytes) -> str:
        """
        Implementación mínima; tu versión real está en whisper_stream.
        """
        try:
            resp = self.client.audio.transcriptions.create(
                file=pcm,
                model="gpt-4o-mini-tts"
            )
            return resp.text
        except Exception:
            return ""

    def tts(self, text: str) -> bytes:
        """
        Implementación mínima para TTS.
        """
        try:
            resp = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text
            )
            return resp.read()
        except Exception:
            return b""
