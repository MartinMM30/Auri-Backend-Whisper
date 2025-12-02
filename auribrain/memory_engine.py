# auribrain/memory_engine.py

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
import json
import os


@dataclass
class MemoryEntry:
    ts: str          # ISO8601
    role: str        # "user" | "assistant"
    text: str
    intent: Optional[str] = None


class MemoryEngine:
    """
    Memoria de Auri:
    - reciente: últimas N interacciones (para el prompt)
    - facts: lista de frases largas sobre el usuario (largo plazo simple)
    - persistencia básica en disco (JSON)
    """

    def __init__(self, persist_path: str = "data/memory.json", max_recent: int = 30):
        self.persist_path = persist_path
        self.max_recent = max_recent

        self.recent: List[MemoryEntry] = []
        self.facts: List[str] = []

        self._load()

    # ---------------------------------------------------------
    # PERSISTENCIA
    # ---------------------------------------------------------
    def _load(self):
        try:
            if not os.path.exists(self.persist_path):
                return

            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.recent = [
                MemoryEntry(**item) for item in data.get("recent", [])
            ]
            self.facts = data.get("facts", [])
        except Exception as e:
            print(f"[MemoryEngine] Error cargando memoria: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            data = {
                "recent": [asdict(m) for m in self.recent],
                "facts": self.facts,
            }
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryEngine] Error guardando memoria: {e}")

    # ---------------------------------------------------------
    # API PRINCIPAL
    # ---------------------------------------------------------
    def add_interaction(
        self,
        user_msg: str,
        assistant_msg: Optional[str] = None,
        intent: Optional[str] = None,
    ):
        """
        Guarda una interacción:
        - Siempre añade el mensaje del usuario.
        - Opcionalmente añade la respuesta de Auri.
        """
        now = datetime.utcnow().isoformat()

        self.recent.append(
            MemoryEntry(ts=now, role="user", text=user_msg, intent=intent)
        )

        if assistant_msg:
            self.recent.append(
                MemoryEntry(ts=now, role="assistant", text=assistant_msg, intent=intent)
            )

        # Mantener solo N últimos
        if len(self.recent) > self.max_recent:
            self.recent = self.recent[-self.max_recent :]

        self._save()

    def get_recent_dialog(self, n: int = 8) -> str:
        """
        Devuelve una versión texto de las últimas N interacciones.
        Útil para meter al prompt.
        """
        tail = self.recent[-(n * 2) :]  # user+assistant
        lines = []
        for m in tail:
            prefix = "Usuario" if m.role == "user" else "Auri"
            lines.append(f"{prefix}: {m.text}")
        return "\n".join(lines)

    def add_fact(self, fact: str):
        """
        Añade un dato persistente sobre el usuario.
        (ej: “Le encanta programar de noche”, “Vive en Cot, Cartago”.)
        Por ahora lo puedes llamar manualmente desde otros módulos.
        """
        fact = fact.strip()
        if not fact:
            return
        # Evitar duplicados simples
        if fact not in self.facts:
            self.facts.append(fact)
            self._save()

    def get_facts(self) -> str:
        if not self.facts:
            return ""
        return "\n".join(f"- {f}" for f in self.facts)
