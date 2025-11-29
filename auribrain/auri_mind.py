from openai import OpenAI
from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine

class AuriMind:
    """
    Núcleo de inteligencia de Auri.
    - Detecta intención
    - Observa contexto (clima, hora, carga mental)
    - Analiza emociones del usuario
    - Usa la personalidad elegida (Jarvis, Classic, Friendly…)
    - Produce reasoning → respuesta final humana
    """

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine()
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()

    # -------------------------------------------------------------------
    # 🧠 THINK — produce razonamiento + respuesta Jarvis
    # -------------------------------------------------------------------
    def think(self, user_msg: str):
        if not user_msg.strip():
            return {
                "intent": "unknown",
                "raw": "",
                "final": "Perdón, no logré escucharte. ¿Podrías repetirlo?"
            }

        # 1) Registrar interacción en memoria
        self.memory.add_interaction(user_msg)

        # 2) Detectar intención híbrida (reglas + LLM)
        intent = self.intent.detect(user_msg)

        # 3) Obtener contexto del día
        ctx = self.context.get_daily_context()

        # 4) Analizar personalidad activa
        style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        # 5) Prompt Jarvis híbrido
        system_prompt = (
            f"Eres Auri, un asistente personal avanzado con estilo '{self.personality.current}'. "
            f"Tu tono es: {style['tone']}. "
            f"Rasgos clave: {', '.join(style['traits'])}. "
            f"Hablas con elegancia, precisión y calidez humana. "
            f"Analiza contexto, emociones y carga del usuario antes de responder. "
            f"No menciones que eres una IA. "
            f"Tu objetivo es ser un verdadero asistente al estilo Jarvis."
        )

        # 6) Llamada a LLM para reasoning
        raw = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = raw.choices[0].message["content"]

        # 7) Procesar respuesta final
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
