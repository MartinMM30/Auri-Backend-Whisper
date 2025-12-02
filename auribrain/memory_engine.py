# auribrain/memory_engine.py
# MemoryEngine V6 – Memoria reciente + integración MongoDB

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

from auribrain.memory_orchestrator import MemoryOrchestrator


@dataclass
class MemoryEntry:
    ts: str          # ISO8601
    role: str        # "user" | "assistant"
    text: str
    intent: Optional[str] = None


class MemoryEngine:
    """
    V6 Memory Engine:
    - Mantiene memoria reciente en RAM (máx 30 interacciones).
    - Envía datos importantes a MongoDB usando MemoryOrchestrator.
    - Integra facts + semantic memory (vectores).
    """

    def __init__(self, user_id: str, max_recent: int = 30):
        self.user_id = user_id
        self.max_recent = max_recent

        self.recent: List[MemoryEntry] = []
        self.orch = MemoryOrchestrator()   # Orquestador MongoDB

    # ---------------------------------------------------------
    # MEMORIA RECIENTE (contexto conversacional)
    # ---------------------------------------------------------
    def add_interaction(
        self,
        user_msg: str,
        assistant_msg: Optional[str] = None,
        intent: Optional[str] = None,
    ):
        """Guarda una interacción en memoria reciente + analiza si debe guardarse en MongoDB."""

        now = datetime.utcnow().isoformat()

        # --- Mensaje del usuario ---
        entry_user = MemoryEntry(
            ts=now,
            role="user",
            text=user_msg,
            intent=intent,
        )
        self.recent.append(entry_user)

        # --- Mensaje de Auri ---
        if assistant_msg:
            entry_assistant = MemoryEntry(
                ts=now,
                role="assistant",
                text=assistant_msg,
                intent=intent,
            )
            self.recent.append(entry_assistant)

        # Limitar cantidad
        if len(self.recent) > self.max_recent:
            self.recent = self.recent[-self.max_recent :]

        # Analizar si este mensaje tiene un “hecho” del usuario
        self._maybe_save_fact(user_msg)

        # Guardar vector semántico
        self._save_semantic_memory(user_msg)

    # ---------------------------------------------------------
    # DETECCIÓN DE HECHOS EXPLÍCITOS
    # ---------------------------------------------------------
    def _maybe_save_fact(self, text: str):
        """
        Extrae hechos importantes del mensaje del usuario mediante reglas simples.
        Puedes expandirlo más adelante.
        """
        t = text.lower()

        # Nombre
        if "mi nombre es" in t:
            name = t.split("mi nombre es")[-1].strip()
            self.orch.add_fact(self.user_id, f"El usuario se llama {name}")

        # Lugar
        if "vivo en" in t:
            place = t.split("vivo en")[-1].strip()
            self.orch.add_fact(self.user_id, f"Vive en {place}")

        # Color favorito
        if "mi color favorito es" in t:
            color = t.split("es")[-1].strip()
            self.orch.add_fact(self.user_id, f"Su color favorito es {color}")

        # Puedes añadir más reglas naturalmente.

    # ---------------------------------------------------------
    # SEMANTIC MEMORY (VECTOR STORAGE)
    # ---------------------------------------------------------
    def _save_semantic_memory(self, text: str):
        """
        Guarda el mensaje como vector para búsquedas futuras tipo RAG.
        """
        if len(text.split()) < 3:
            # Muy pequeño → no aporta
            return

        self.orch.add_vector(self.user_id, text)

    # ---------------------------------------------------------
    # EXPORTAR MEMORIA RECIENTE PARA EL PROMPT
    # ---------------------------------------------------------
    def get_recent_dialog(self, n: int = 8) -> str:
        """Devuelve las últimas N interacciones en formato texto."""
        tail = self.recent[-(n * 2) :]  # user + assistant

        lines = []
        for m in tail:
            prefix = "Usuario" if m.role == "user" else "Auri"
            lines.append(f"{prefix}: {m.text}")

        return "\n".join(lines)

    # ---------------------------------------------------------
    # RAG (consulta recuerdos de MongoDB)
    # ---------------------------------------------------------
    def search_long_term(self, query: str):
        """Devuelve recuerdos relevantes desde MongoDB."""
        return self.orch.search(self.user_id, query)

    def get_facts(self):
        """Devuelve facts del usuario almacenados."""
        return self.orch.get_facts(self.user_id)

    def get_profile(self):
        """Devuelve perfil guardado del usuario."""
        return self.orch.get_user_profile(self.user_id)
