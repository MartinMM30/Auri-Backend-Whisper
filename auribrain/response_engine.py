# auribrain/response_engine.py

class ResponseEngine:
  def __init__(self):
    pass

  # -------------------------------------------------------------------
  # Plantillas base por intención
  # -------------------------------------------------------------------
  def intent_templates(self):
    return {
      "reminder.create": "Te ayudo con ese recordatorio.",
      "reminder.remove": "Puedo quitar ese recordatorio.",
      "weather.query": "Te cuento cómo está el clima.",
      "outfit.suggest": "Déjame ver qué te recomiendo.",
      "user.state": "Estoy atento a cómo te sientes.",
      "emotion.support": "Estoy aquí contigo.",
      "auri.config": "Claro, ajustemos tu configuración.",
      "knowledge.query": "Déjame explicártelo.",
      "smalltalk.greeting": "Claro, hablemos.",
      "fun.joke": "Aquí va uno.",
      "conversation.general": "Te respondo a eso.",
      "unknown": "Lo estoy pensando un momento.",
    }

  # -------------------------------------------------------------------
  # Respuesta final combinando contexto + memoria + estilo + LLM
  # -------------------------------------------------------------------
  def build(self, intent, style, context, memory, user_msg, raw_answer):
    tone = style.get("tone", "")
    traits = style.get("traits", [])

    base = self.intent_templates()
    intent_base = base.get(intent, base["unknown"])

    # ---------- 2. Texto de contexto (más suave) ----------
    ctx_parts = []

    weather = context.get("weather", "").lower()
    tod = context.get("time_of_day", "")
    energy = context.get("energy", "")
    workload = context.get("workload", "")

    if "rain" in weather:
      ctx_parts.append("Parece que afuera está lluvioso.")
    elif "sun" in weather:
      ctx_parts.append("El clima está bastante agradable.")

    if tod == "night":
      ctx_parts.append("Ya es de noche, intento ser más breve.")
    elif tod == "morning":
      ctx_parts.append("Es una buena mañana.")

    if energy == "low":
      ctx_parts.append("Trataré de no abrumarte.")
    elif energy == "high":
      ctx_parts.append("Aprovechemos que tienes buena energía.")

    if workload == "busy":
      ctx_parts.append("Veo que tienes bastantes cosas por hacer.")
    elif workload == "overloaded":
      ctx_parts.append("Tu agenda está cargada, puedo ayudarte a ordenar.")

    context_sentence = " ".join(ctx_parts)

    # ---------- 3. Sin repetir literalmente el mensaje del usuario ----------
    # (El system prompt ya indica no recapitular, así que no añadimos mem_line)

    final = f"{intent_base} "

    if context_sentence:
      final += context_sentence + " "

    final += f"({tone}). {raw_answer.strip()}"

    final = self._humanize(final)
    return final.strip()

  # -------------------------------------------------------------------
  # Suavizador
  # -------------------------------------------------------------------
  def _humanize(self, text):
    replacements = {
      "Estoy procesando": "Déjame pensarlo un momento",
      "Aquí tienes mi respuesta": "Te cuento lo que he pensado",
      "Te explico": "Mira, lo veo así",
    }

    for k, v in replacements.items():
      text = text.replace(k, v)

    while "  " in text:
      text = text.replace("  ", " ")

    return text
