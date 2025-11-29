class EmotionalEngine:
    """
    Genera señales de lip-sync o "estado" del slime.
    """

    @staticmethod
    def lip_sync_from_text(text: str):
        # Simula energía de voz según caracteres
        energy = min(1.0, max(0.05, len(text) % 10 / 10))
        return {
            "type": "lip_sync",
            "energy": energy
        }

    @staticmethod
    def thinking(state: bool):
        return {
            "type": "thinking",
            "state": state
        }
