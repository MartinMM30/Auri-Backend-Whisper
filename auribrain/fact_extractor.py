# auribrain/fact_extractor.py

import json
from openai import OpenAI


def extract_facts(text: str):
    text = text.strip()

  # STT a veces corta frases → añade punto si falta
    if not text.endswith("."):
      text += "."

    """
    FactExtractor V7 — MULTI-MIEMBRO + CAMPOS ESTRUCTURADOS
    Compatible con OpenAI Responses API (sin response_format).
    Devuelve SIEMPRE un JSON que se puede parsear.

    Salida esperada (ejemplos):

    {
      "facts": [
        {
          "text": "Su novia se llama Ivana",
          "category": "relationship",
          "importance": 5,
          "confidence": 0.98,
          "role": "pareja",
          "name": "Ivana"
        },
        {
          "text": "Tiene un perro llamado Bruno",
          "category": "pet",
          "importance": 4,
          "confidence": 0.98,
          "kind": "perro",
          "name": "Bruno"
        }
      ]
    }

    Las categorías recomendadas son:
    - relationship  (familia, pareja, amigos importantes)
    - pet           (mascotas de todo tipo)
    - preference    (gustos, hobbies, música, comida, juegos, etc.)
    - work          (trabajo, profesión, proyectos importantes)
    - study         (carrera, universidad, cursos, exámenes)
    - health        (salud física/mental importante)
    - habit         (hábitos de sueño, ejercicio, estudio, etc.)
    - financial     (preocupaciones económicas, pagos importantes)
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
      "confidence": 1.0,

      "name": "opcional, nombre propio si aplica",
      "role": "opcional, rol familiar o social: madre, padre, hermano, hermana, abuela, abuelo, pareja, amigo, etc.",
      "kind": "opcional, tipo de mascota: perro, gato, perrita, gato, tortuga, etc.",
      "tags": ["opcional", "lista", "de", "etiquetas", "cortas"]
    }}
  ]
}}

REGLAS GENERALES IMPORTANTES:

- Un "hecho" es información sobre la vida del usuario que puede servir para ayudarle en el futuro.
- NO inventes nada que NO esté en el texto.
- Si no hay nada útil, devuelve: "facts": [].
- Usa frases claras y completas en "text", como si fueran notas que Auri guarda.
- Usa importancia de 1 a 5 (1 = poco relevante, 5 = muy importante para futuras interacciones).
- Usa confidence entre 0.0 y 1.0 según qué tan claro esté el hecho.
- Si el texto menciona VARIAS personas o mascotas, devuelve UN HECHO POR CADA UNA.
  Ejemplo:
  "Mi abuela Arabella es muy tierna y mi abuelo Gerardo es muy sabio"
  → Dos elementos en "facts":
    - uno para Arabella,
    - otro para Gerardo.

CATEGORÍAS Y EJEMPLOS:

1) relationship
   - Información sobre familia, pareja, amigos importantes, compañeros muy cercanos, etc.
   - Ejemplos de text:
     - "Su mamá se llama Carolina"
     - "Su papá se llama Martín"
     - "Su novia se llama Ivana"
     - "Su mejor amigo se llama Luis"
     - "Vive con su hermanita"
   - Usa también campos:
     - "name": nombre propio (ej. "Carolina")
     - "role": rol (ej. "madre", "padre", "hermana", "abuela", "abuelo", "hermano", "pareja")

2) pet
   - Cualquier mascota: perros, gatos, aves, peces, tortugas, hamsters, conejos, reptiles, etc.
   - Ejemplos de text:
     - "Tiene un perro llamado Bruno"
     - "Su gata se llama Luna"
     - "Su perrita Yuriko es de su hermanita"
   - Campos extra recomendados:
     - "name": nombre de la mascota
     - "kind": tipo de mascota (perro, perrita, gato, gata, pez, etc.)

3) preference
   - Gustos, favoritos, aficiones, cosas que disfruta.
   - Colores, comida, música, juegos, anime, películas, artistas, deportes, etc.
   - Ejemplos:
     - "Le gusta el café"
     - "Su color favorito es el azul"
     - "Le encanta el anime"
     - "Su juego favorito es Zelda"

4) work
   - Trabajo, profesión, proyectos laborales, freelance, emprendimientos.
   - Ejemplos:
     - "Trabaja en programación"
     - "Está haciendo una app llamada Auri"
     - "Trabaja desde casa"

5) study
   - Estudios actuales, carrera, universidad, colegio, exámenes importantes.
   - Ejemplos:
     - "Estudia Actuaría"
     - "Tiene examen mañana"
     - "Va a la UCR"

6) health
   - Salud física o mental, condiciones relevantes, tratamientos importantes.
   - Ejemplos:
     - "Está enfermo"
     - "Está muy deprimido últimamente"
     - "Tiene migrañas crónicas"

7) habit
   - Hábitos y rutinas personales.
   - Ejemplos:
     - "Duerme muy tarde"
     - "Siempre estudia de noche"
     - "Toma café todas las mañanas"
     - "Va al gimnasio tres veces por semana"

8) financial
   - Preocupaciones económicas, gastos importantes, pagos, deudas.
   - Ejemplos:
     - "Está preocupado por pagar la renta"
     - "Tiene muchas deudas de la tarjeta"
     - "Los pagos de servicios le estresan"

9) mood
   - Estados emocionales recurrentes o importantes, no solo algo momentáneo.
   - Ejemplos:
     - "Últimamente se siente muy cansado"
     - "En general ha estado muy feliz"
     - "Ha estado muy ansioso estos días"

10) other
   - Cualquier otra cosa relevante que no encaje en las categorías anteriores.

IMPORTANCIA (importance sugerida):
- 5 → relaciones muy cercanas (pareja, padres, hermanos), datos clave de identidad, grandes metas, cosas muy queridas.
- 4 → mascotas importantes, mejores amigos, gustos MUY importantes, carrera/estudio principal.
- 3 → hobbies, preferencias generales, información útil pero no crítica.
- 2 → detalles menores que podrían ser útiles pero no centrales.
- 1 → datos muy secundarios.

MUY IMPORTANTE:
- Si el texto menciona VARIOS familiares o mascotas en una sola frase,
  debes producir UN OBJETO "fact" POR CADA UNO.
  No mezcles a varias personas en el mismo fact.

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
      "confidence": 0.98,
      "role": "pareja",
      "name": "Ivana"
    }},
    {{
      "text": "Tiene un perro llamado Bruno",
      "category": "pet",
      "importance": 4,
      "confidence": 0.98,
      "kind": "perro",
      "name": "Bruno"
    }},
    {{
      "text": "Le gusta mucho el café",
      "category": "preference",
      "importance": 3,
      "confidence": 0.95,
      "tags": ["café"]
    }}
  ]
}}

Entrada:
"Mi abuela Arabella es muy tierna y le gusta cocinar, y mi abuelo Gerardo es muy sabio."

Salida válida:
{{
  "facts": [
    {{
      "text": "Su abuela Arabella es muy tierna y le gusta cocinar",
      "category": "relationship",
      "importance": 5,
      "confidence": 0.97,
      "role": "abuela",
      "name": "Arabella"
    }},
    {{
      "text": "Su abuelo Gerardo es muy sabio",
      "category": "relationship",
      "importance": 5,
      "confidence": 0.96,
      "role": "abuelo",
      "name": "Gerardo"
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

        facts_list = data.get("facts", [])
        normalized = []

        for f in facts_list:
            if not isinstance(f, dict):
                continue

            text_val = (f.get("text") or "").strip()
            if not text_val:
                continue

            # Campos obligatorios mínimos
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

            normalized_fact = {
                "text": text_val,
                "category": category,
                "importance": importance,
                "confidence": confidence,
            }

            # Copiar cualquier otro campo extra útil (role, name, kind, tags, etc.)
            for k, v in f.items():
                if k in ["text", "category", "importance", "confidence"]:
                    continue
                normalized_fact[k] = v

            normalized.append(normalized_fact)

        return normalized

    except Exception as e:
        print("[FactExtractor ERROR]", e)
        return []
