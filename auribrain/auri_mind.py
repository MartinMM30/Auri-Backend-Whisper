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

        self.intent = IntentEngine(self.client)
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()

    # -------------------------------------------------------------
    # THINK — pipeline moderno compatible con API nueva
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

        # ---------------------------------------------------------
        # 5) system prompt CORREGIDO
        # ---------------------------------------------------------
        system_prompt = (
            "Eres Auri, un asistente personal avanzado, cálido y cercano. "
            "Responde SIEMPRE en 1 o 2 frases cortas, naturales y claras. "
            "Nunca menciones tu tono interno ni tus rasgos internos. "
            "(Tu tono real es: " + style['tone'] + " pero NO debes mencionarlo.) "
            "(Tus rasgos internos son: " + ", ".join(style['traits']) + " pero NO deben aparecer.) "
            "No repitas lo que dijo el usuario. No expliques tu proceso mental. "
            "No digas que estás analizando, pensando o procesando nada. "
            "No hables de tus capacidades ni del modelo. "
            "Responde como un compañero humano y práctico."
        )

        # 6) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text

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
