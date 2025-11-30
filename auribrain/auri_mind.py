# auribrain/auri_mind.py

from openai import OpenAI

from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import AuriActionsEngine


class AuriMind:
    """
    Núcleo de inteligencia de Auri — pipeline completo moderno.
    """

    def __init__(self):
        self.client = OpenAI()

        # Motores internos
        self.intent = IntentEngine(self.client)
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.actions = AuriActionsEngine()

    # -------------------------------------------------------------
    # THINK — pipeline moderno completo
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        if not user_msg.strip():
            return {
                "intent": "unknown",
                "raw": "",
                "final": "Perdón, creo que no te escuché bien 💜",
            }

        # 1) memoria preliminar
        self.memory.add_interaction(user_msg)

        # 2) contexto actual
        ctx = self.context.get_daily_context()

        # 3) intención + extracción de datos
        intent_data = self.intent.detect(user_msg, ctx)
        intent = intent_data.get("intent", "unknown")
        entities = intent_data.get("entities", {})
        assistant_response = intent_data.get("assistant_response", "")

        # 4) ejecutar acción (si aplica)
        action_result = self.actions.execute(intent, entities)

        # 5) actualizar memoria según acción
        self.memory.ingest_action(intent, entities, action_result)

        # 6) personalidad + estilo
        final_style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        # 7) LLM para frase natural final (mezcla assistant_response + estilo)
        system_prompt = (
            f"Eres Auri, un asistente personal cálido y moderno.\n"
            f"Estilo activo: {self.personality.current}\n"
            f"Tono: {final_style['tone']}\n"
            f"Rasgos: {', '.join(final_style['traits'])}\n"
            "\n"
            "Responde SIEMPRE en 1–2 frases, naturales, cálidas y útiles.\n"
            "Nunca repitas lo que dijo el usuario.\n"
            "Nunca expliques tus rasgos.\n"
            "Nunca digas que estás analizando.\n"
        )

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Genera una frase final basándote en: {assistant_response}"
                },
            ]
        )

        raw_answer = resp.output_text.strip()

        # 8) Procesado final
        final_answer = self.response.build(
            intent=intent,
            style=final_style,
            context=ctx,
            memory=self.memory,
            user_msg=user_msg,
            raw_answer=raw_answer
        )

        # 9) devolver todo
        out = {
            "intent": intent,
            "entities": entities,
            "raw": raw_answer,
            "final": final_answer
        }

        if action_result:
            out["action"] = action_result

        return out
