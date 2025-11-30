from openai import OpenAI
from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine

class AuriMind:
    """
    Núcleo de inteligencia de Auri.
    """

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine()
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()

    # -------------------------------------------------------------
    # THINK — pipeline moderno compatible con la API nueva
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        if not user_msg.strip():
            return {
                "intent": "unknown",
                "raw": "",
                "final": "Perdón, no logré escucharte. ¿Podrías repetirlo?"
            }

        # 1) memoria
        self.memory.add_interaction(user_msg)

        # 2) intención
        intent = self.intent.detect(user_msg)

        # 3) contexto
        ctx = self.context.get_daily_context()

        # 4) personalidad final
        style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        # 5) system prompt moderno
        system_prompt = (
    f"Eres Auri, un asistente personal avanzado con estilo '{self.personality.current}'. "
    f"Tu tono es: {style['tone']}. "
    f"Rasgos clave: {', '.join(style['traits'])}. "
    "Responde SIEMPRE en 1 o 2 frases como máximo, naturales y claras. "
    "No repitas literalmente lo que dijo el usuario. "
    "No recapitules conversaciones anteriores. "
    "No expliques tu tono ni tus rasgos en la respuesta. "
    "No digas que estás analizando, ni que vas a organizar el día, "
    "a menos que el usuario lo pida explícitamente. "
    "No menciones que eres una IA; responde como un compañero cercano y práctico."
)

        # 6) LLM moderno — API responses.create()
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text  # <- forma correcta en API moderna

        # 7) procesado final
        final_answer = self.response.build(
            intent=intent,
            style=style,
            context=ctx,
            memory=self.memory,
            user_msg=user_msg,
            raw_answer=raw_answer
        )

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer
        }
