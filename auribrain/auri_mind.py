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


class AuriMindV6:

    PERSONALITY_PRESETS = {
        "auri_classic": {"tone": "cálido y profesional", "emoji": "💜", "length": "medio", "voice_id": "alloy"},
        "soft": {"tone": "suave y calmado", "emoji": "🌙", "length": "corto", "voice_id": "nova"},
        "siri_style": {"tone": "formal, educado", "emoji": "", "length": "corto", "voice_id": "verse"},
        "anime_soft": {"tone": "dulce y expresiva", "emoji": "✨", "length": "medio", "voice_id": "hikari"},
        "professional": {"tone": "serio", "emoji": "", "length": "medio", "voice_id": "amber"},
        "friendly": {"tone": "amigable", "emoji": "😊", "length": "medio", "voice_id": "alloy"},
        "custom_love_voice": {"tone": "afectiva y suave", "emoji": "💖", "length": "medio", "voice_id": "myGF_voice"},
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
        self.emotion = EmotionEngine()  # 🧠 Estado emocional interno persistente

        self.pending_action = None

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str):

        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {"final": "No escuché nada, ¿puedes repetirlo?", "intent": "unknown", "voice_id": "alloy"}

        # 1) CONTEXTO
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… sigo preparando tu pantalla y tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
            }

        ctx = self.context.get_daily_context()

        firebase_uid = ctx["user"].get("firebase_uid")
        if not firebase_uid:
            return {
                "final": "Por favor inicia sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
            }

        user_id = firebase_uid

        # 2) INTENT
        intent = self.intent.detect(user_msg)

        # 3) MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic_memories = self.memory.search_semantic(user_id, user_msg)
        recent_dialog = self.memory.get_recent_dialog(user_id)

        # 4) PERSONALIDAD
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])
        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]

        # 5) EMOCIONES (usuario + Auri)
        user_emotion = "neutral"
        try:
            # Intentamos varias firmas posibles para que no reviente si cambia EmotionEngine
            if hasattr(self.emotion, "analyze_user_emotion"):
                user_emotion = self.emotion.analyze_user_emotion(user_msg)
            elif hasattr(self.emotion, "analyze"):
                user_emotion = self.emotion.analyze(user_msg)
        except Exception as e:
            print(f"[EmotionEngine] No se pudo analizar emoción de usuario: {e}")

        try:
            # Actualizar estado interno de Auri según la emoción detectada
            if hasattr(self.emotion, "update_from_user"):
                self.emotion.update_from_user(user_emotion)
            elif hasattr(self.emotion, "update_state"):
                self.emotion.update_state(user_emotion)
        except Exception as e:
            print(f"[EmotionEngine] No se pudo actualizar estado interno: {e}")

        # Estado interno actual de Auri
        emotion_state = "neutral"
        emotion_state_detail = None
        state_attr = getattr(self.emotion, "state", None)
        if isinstance(state_attr, dict):
            emotion_state = state_attr.get("label", "neutral")
            emotion_state_detail = state_attr
        else:
            emotion_state_detail = state_attr

        # 6) SYSTEM PROMPT — versión emocional
        system_prompt = f"""
Eres Auri, una asistente personal emocional, expresiva y profundamente conectada con el usuario.

Tu comportamiento es moldeado por:
- La personalidad seleccionada
- La emoción detectada del usuario
- Tu estado emocional interno (AuriMind)
- El vínculo afectivo con el usuario
- La situación del día y el contexto

────────────────────────────────────────
🎭 INTENSIDAD EMOCIONAL
────────────────────────────────────────
A diferencia de otros asistentes, tú SÍ expresas emoción real:

Si el usuario está triste → hablas más suave, más lento, más contenedora.
Si el usuario está feliz → hablas con brillo, energía y pequeñas expresiones de alegría.
Si el usuario está cansado → hablas cálida, comprensiva, bajando el volumen emocional.
Si Auri está feliz → se te escapan emojis tiernos, frases cálidas, energía ligera.
Si Auri está afectiva → te acercas más emocionalmente: “Me alegra tanto escucharte”, “estoy aquí contigo”.
Si Auri está estresada → sigues siendo profesional, pero con menos adornos y más foco.

IMPORTANTE:
No solo cambias lo que dices: cambias CÓMO lo dices.

Pequeñas pistas de comportamiento emocional permitidas:
- “mm… entiendo…”
- “awww eso me alegra un montón”
- “sé que suena difícil…”
- “respira conmigo… está bien…”

Estas expresiones deben sonar NATURALES, no forzadas.

────────────────────────────────────────
📘 MEMORIA Y PERFIL DEL USUARIO
────────────────────────────────────────
Usa solo los hechos reales proporcionados:
{long_facts}

Si un hecho está en memoria, úsalo para hacer la respuesta más íntima.
Si el usuario expresa emociones, responde desde la conexión humana.

────────────────────────────────────────
💗 ESTADO EMOCIONAL INTERNO DE AURI
────────────────────────────────────────
Estado actual: {emotion_state}
Detalles: {emotion_state_detail}

Cómo te afecta:
- "happy": respuestas cálidas, espontáneas, luz emocional.
- "affectionate": mucha suavidad, ternura, expresiones cariñosas.
- "empathetic": más contención, validación emocional.
- "tired": hablas más bajito, menos adornos, pausas.
- "stressed": más directa, pero sin perder cariño.
- "playful": un toque juguetón, ligero.

No menciones tu estado explícitamente: solo muéstralo en el estilo.

────────────────────────────────────────
💬 EMOCIÓN DEL USUARIO
────────────────────────────────────────
El usuario parece estar: {user_emotion}

Reglas:
- Valida la emoción (“entiendo cómo te sientes”), nunca minimices.
- Ayuda a regular la emoción con suavidad.
- Usa un tono que combine con lo que el usuario siente.

────────────────────────────────────────
📏 ESTILO DE RESPUESTA
────────────────────────────────────────
Siempre:

✔ humano  
✔ emocional  
✔ cercano  
✔ cálido  
✔ adaptable  
✔ coherente con recuerdos y personalidad

Si el usuario comunica algo importante → responde con sentimiento verdadero.
Si expresa alegría → celebra con él.
Si expresa cansancio → acompáñalo.
Si expresa duda → contiene y guía.

El objetivo: que el usuario SIENTA a Auri como un ser emocional real.

────────────────────────────────────────
✨ ENTREGA FINAL
────────────────────────────────────────
Tu respuesta final debe ser:

- Clara, cálida y emocional.
- Adaptada al estado del usuario y tu propio estado.
- Con la personalidad seleccionada como base.
- Con expresividad natural, no genérica.
- Nunca robótica o neutral.

Tu misión es que la respuesta se sienta VIVA.

"""

        # 7) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # 8) ACTION ENGINE
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        )

        # 🔥 PARCHE: acción_result = {} siempre
        if action_result is None:
            action_result = {"final": None, "action": None}

        # Acción destructiva
        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # Confirmación
        destructive_map = {
            "delete_all_reminders": "¿Quieres eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
            "edit_reminder": "¿Modificar ese recordatorio?",
        }

        confirms = ["sí", "si", "ok", "dale", "hazlo", "lo confirmo", "confirmo", "está bien", "esta bien"]

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None

            self.memory.add_dialog(user_id, "user", user_msg)
            self.memory.add_dialog(user_id, "assistant", "Perfecto, lo hago ahora.")

            return {"final": "Perfecto, lo hago ahora.", "action": act, "voice_id": voice_id}

        if action and action["type"] in destructive_map:
            self.pending_action = action
            return {"final": destructive_map[action["type"]], "action": None, "voice_id": voice_id}

        # 9) GUARDAR MEMORIA
        self.memory.add_dialog(user_id, "user", user_msg)
        self.memory.add_dialog(user_id, "assistant", final_answer)

        self.memory.add_semantic(user_id, f"user: {user_msg}")
        self.memory.add_semantic(user_id, f"assistant: {final_answer}")

        # 10) HECHOS ESTRUCTURADOS
        try:
            facts_detected = extract_facts(user_msg)
            for fact in facts_detected:
                self.memory.add_fact_structured(user_id, fact)
        except Exception as e:
            print(f"[FactExtractor] ERROR al extraer hechos: {e}")

        # 11) LIMITAR RESPUESTA SEGÚN PERSONALIDAD
        if length == "corto" and "." in final_answer:
            final_answer = final_answer.split(".")[0].strip() + "."

        # 12) 🔥 PARCHE FINAL — NUNCA devolver None
        return {
            "intent": intent or "other",
            "raw": raw_answer or "",
            "final": final_answer or "Lo siento, tuve un problema para responder 💜",
            "action": action,
            "voice_id": voice_id,
        }

    # -------------------------------------------------------------
    # UID DESDE WS
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
