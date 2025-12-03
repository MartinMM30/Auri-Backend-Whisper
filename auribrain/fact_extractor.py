# auribrain/fact_extractor.py

import json
from openai import OpenAI


def extract_facts(text: str):
    """
    FactExtractor V6 – EXTENDIDO
    Compatible con OpenAI Responses API (sin response_format).
    Devuelve SIEMPRE un JSON que se puede parsear.

    Salida esperada (ejemplo):

    {
      "facts": [
        {
          "text": "Mi novia se llama Ivana",
          "category": "relationship",
          "importance": 5,
          "confidence": 0.95
        }
      ]
    }

    Las categorías recomendadas son:
    - relationship  (familia, pareja, amigos importantes)
    - pet           (mascotas de todo tipo)
    - preference    (gustos, colores favoritos, hobbies, música, comida, juegos, etc.)
    - work          (trabajo, profesión, proyectos importantes)
    - study         (carrera, universidad, cursos, exámenes)
    - health        (salud física/mental, medicación, condiciones importantes)
    - habit         (hábitos de sueño, ejercicio, estudio, café, etc.)
    - financial     (preocupaciones económicas, deudas, pagos importantes)
    - mood          (estado emocional estable/recurrente)
    - other         (todo lo demás)
    """

    client = OpenAI()

    system_msg = (
        "Eres un extractor de hechos personales del usuario. "
        "Debes devolver EXCLUSIVAMENTE un JSON válido. "
        "No incluyas explicaciones, solo JSON. "
        "La palabra 'json' ya está incluida aquí para ayudarte a entender el formato."
    )

    user_prompt = f"""
Extrae HECHOS personales del usuario desde el texto dado.

Debes devolver SIEMPRE un objeto JSON con la forma:

{{
  "facts": [
    {{
      "text": "hecho en lenguaje natural",
      "category": "relationship | pet | preference | work | study | health | habit | financial | mood | other",
      "importance": 1,
      "confidence": 1.0
    }}
  ]
}}

REGLAS GENERALES:
- Un "hecho" es información sobre la vida del usuario que puede servir para ayudarle en el futuro.
- No inventes nada que NO esté en el texto.
- Si no hay nada útil, devuelve: "facts": [].
- Usa frases claras y completas en "text", como si fueran notas que Auri guarda.
- Usa importancia de 1 a 5 (1 = poco relevante, 5 = muy importante para futuras interacciones).
- Usa confidence entre 0.0 y 1.0 según qué tan claro esté el hecho.

CATEGORÍAS Y EJEMPLOS:

1) relationship
   - Información sobre familia, pareja, amigos importantes, compañeros muy cercanos, etc.
   - Ejemplos:
     - "Mi mamá se llama Carolina"
     - "Mi papá se llama Martín"
     - "Mi novia se llama Ivana"
     - "Mi mejor amigo se llama Luis"
     - "Vivo con mi hermanita"

2) pet
   - Cualquier mascota: perros, gatos, aves, peces, tortugas, hamsters, conejos, reptiles, etc.
   - Ejemplos:
     - "Tengo un perro que se llama Bruno"
     - "Mi gata se llama Luna"
     - "Mi perrita Yuriko es de mi hermanita"
     - "Tengo un pez llamado Nemo"

3) preference
   - Gustos, favoritos, aficiones, cosas que disfruta.
   - Colores, comida, música, juegos, anime, películas, artistas, deportes, etc.
   - Ejemplos:
     - "Me gusta el café"
     - "Mi color favorito es el azul"
     - "Me encanta el anime"
     - "Mi juego favorito es Zelda"
     - "Me gusta escuchar k-pop"

4) work
   - Trabajo, profesión, proyectos laborales, freelance, emprendimientos.
   - Ejemplos:
     - "Trabajo en programación"
     - "Estoy haciendo una app llamada Auri"
     - "Trabajo desde casa"

5) study
   - Estudios actuales, carrera, universidad, colegio, exámenes importantes.
   - Ejemplos:
     - "Estudio Actuaría"
     - "Tengo examen mañana"
     - "Voy a la UCR"

6) health
   - Salud física o mental, condiciones relevantes, tratamientos importantes.
   - Ejemplos:
     - "Estoy enfermo"
     - "Estoy muy deprimido últimamente"
     - "Tengo migrañas crónicas"

7) habit
   - Hábitos y rutinas personales.
   - Ejemplos:
     - "Duermo muy tarde"
     - "Siempre estudio de noche"
     - "Tomo café todas las mañanas"
     - "Voy al gimnasio tres veces por semana"

8) financial
   - Preocupaciones económicas, gastos importantes, pagos, deudas.
   - Ejemplos:
     - "Estoy preocupado por pagar la renta"
     - "Tengo muchas deudas de la tarjeta"
     - "Los pagos de servicios me estresan"

9) mood
   - Estados emocionales recurrentes o importantes, no solo algo momentáneo.
   - Ejemplos:
     - "Últimamente me siento muy cansado"
     - "En general he estado muy feliz"
     - "He estado muy ansioso estos días"

10) other
   - Cualquier otra cosa relevante que no encaje en las categorías anteriores.

IMPORTANCIA (importance sugerida):
- 5 → relaciones muy cercanas (pareja, padres, hermanos), datos clave de identidad, grandes metas, cosas muy queridas.
- 4 → mascotas importantes, mejores amigos, gustos MUY importantes, carrera/estudio principal.
- 3 → hobbies, preferencias generales, información útil pero no crítica.
- 2 → detalles menores que podrían ser útiles pero no centrales.
- 1 → datos muy secundarios.

EJEMPLOS DE SALIDA:

Entrada:
"Mi novia se llama Ivana y mi perro se llama Bruno. Me gusta mucho el café."

Salida válida:
{{
  "facts": [
    {{
      "text": "Su novia se llama Ivana",
      "category": "relationship",
      "importance": 5,
      "confidence": 0.98
    }},
    {{
      "text": "Tiene un perro llamado Bruno",
      "category": "pet",
      "importance": 4,
      "confidence": 0.98
    }},
    {{
      "text": "Le gusta mucho el café",
      "category": "preference",
      "importance": 3,
      "confidence": 0.95
    }}
  ]
}}

Entrada:
"Estoy muy cansado y estresado por los pagos, pero amo a mis mascotas."

Salida válida:
{{
  "facts": [
    {{
      "text": "Se siente cansado y estresado por los pagos",
      "category": "mood",
      "importance": 4,
      "confidence": 0.9
    }},
    {{
      "text": "Los pagos son una fuente de estrés para él",
      "category": "financial",
      "importance": 4,
      "confidence": 0.9
    }},
    {{
      "text": "Ama a sus mascotas",
      "category": "pet",
      "importance": 4,
      "confidence": 0.9
    }}
  ]
}}

Si el texto no contiene hechos útiles, devuelve:

{{
  "facts": []
}}

TEXTO DEL USUARIO:
\"\"\"{text}\"\"\"
"""

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw = (resp.output_text or "").strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("[FactExtractor] WARNING: El modelo devolvió algo no parseable")
            print(raw)
            return []

        facts = data.get("facts", [])
        # asegurar estructura mínima
        normalized = []
        for f in facts:
            if not isinstance(f, dict):
                continue
            text_val = (f.get("text") or "").strip()
            if not text_val:
                continue

            category = (f.get("category") or "other").strip() or "other"
            importance = f.get("importance", 3)
            confidence = f.get("confidence", 0.8)

            # clamps básicos
            try:
                importance = int(importance)
            except Exception:
                importance = 3
            importance = max(1, min(5, importance))

            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.8
            confidence = max(0.0, min(1.0, confidence))

            normalized.append({
                "text": text_val,
                "category": category,
                "importance": importance,
                "confidence": confidence,
            })

        return normalized

    except Exception as e:
        print("[FactExtractor ERROR]", e)
        return []
