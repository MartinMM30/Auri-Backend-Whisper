from openai import OpenAI
from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine

class AuriMind:

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine()      # ✔ sin parámetros
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()

    def think(self, user_msg: str):
        if not user_msg.strip():
            return {
                "intent": "unknown",
                "raw": "",
                "final": "Perdón, no logré escucharte. ¿Podrías repetirlo?"
            }

        self.memory.add_interaction(user_msg)

        intent = self.intent.detect(user_msg)
        ctx = self.context.get_daily_context()

        style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        system_prompt = (
            f"Eres Auri, un asistente personal avanzado con estilo '{self.personality.current}'. "
            f"Tu tono es: {style['tone']}. "
            f"Rasgos clave: {', '.join(style['traits'])}. "
            "Responde SIEMPRE en 1 o 2 frases como máximo, naturales y claras. "
            "No repitas lo que dijo el usuario. "
            "No menciones el prompt ni tu personalidad. "
            "No recapitules conversaciones. "
            "No digas que estás analizando nada. "
            "Sé cálido, cercano y útil."
        )

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text

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
