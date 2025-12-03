# auribrain/response_engine.py

from auribrain.smart_org_engine import SmartOrganizationEngine

# Motores especiales reales según tu estructura
from auribrain.crisis_engine import CrisisEngine
from auribrain.focus_engine import FocusEngine
from auribrain.sleep_engine import SleepEngine
from auribrain.love_mode_engine import LoveModeEngine
from auribrain.energy_engine import EnergyEngine
from auribrain.slang_mode_engine import SlangModeEngine
from auribrain.journal_engine import JournalEngine


class ResponseEngine:

    def __init__(self):
        self.org = SmartOrganizationEngine()

        # Modos especiales
        self.crisis = CrisisEngine()
        self.focus = FocusEngine()
        self.sleep = SleepEngine()
        self.love = LoveModeEngine()
        self.energy = EnergyEngine()
        self.slang = SlangModeEngine()
        self.journal = JournalEngine()

    # ---------------------------------------------------------------
    # BUILD
    # ---------------------------------------------------------------
    def build(
        self,
        intent,
        style,
        context,
        memory,
        user_msg,
        raw_answer,
        emotion_state,
        emotion_snapshot
    ):
        txt = (user_msg or "").lower().strip()

        energy = float(emotion_snapshot.get("energy", 0.5))
        affection = float(emotion_snapshot.get("affection", 0.4))
        stress = float(emotion_snapshot.get("stress", 0.2))


        # ============================================================
        # 1) CRISIS — PRIORIDAD MÁXIMA
        # ============================================================
        if self.crisis.detect(txt):
            return self.crisis.respond(context)


        # ============================================================
        # 2) MODO SLANG / HUMOR NEGRO SUAVE
        # ============================================================
        slang_mode = self.slang.detect(txt, stress)
        if slang_mode:
            return self.slang.respond(slang_mode)


        # ============================================================
        # 3) MODO SUEÑO
        # ============================================================
        if self.sleep.detect(txt, emotion_state):
            return self.sleep.respond(context, emotion_state)


        # ============================================================
        # 4) MODO PAREJA / LOVE MODE
        # ============================================================
        if self.love.detect(txt, affection):
            return self.love.respond(context)


        # ============================================================
        # 5) MODO FOCUS
        # ============================================================
        if self.focus.detect(txt, energy) or emotion_state in ["stressed", "overwhelmed"]:
            return self.focus.respond(context)


        # ============================================================
        # 6) MODO ENERGÍA
        # ============================================================
        detected_energy_mode = self.energy.detect(txt, energy)
        if detected_energy_mode:
            return self.energy.respond(detected_energy_mode, context)


        # ============================================================
        # 7) JOURNAL EMOCIONAL (solo guarda, no responde)
        # ============================================================
        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            memory.add_semantic(context["user"]["firebase_uid"], entry)
            # NO interrumpe, deja seguir al raw_answer


        # ============================================================
        # 8) MICRO–RESPUESTAS POR EMOCIÓN
        # ============================================================
        if emotion_state in [
            "worried", "stressed", "sad", "angry",
            "tired", "happy", "affectionate"
        ]:
            emotional_help = self.org.analyze(
                emotional_state=emotion_state,
                context=context,
                snapshot=emotion_snapshot
            )
            return emotional_help + "\n\n" + raw_answer


        # ============================================================
        # 9) QA SIMPLES
        # ============================================================
        user = context.get("user", {})
        weather = context.get("weather", {})

        # Nombre
        if "mi nombre" in txt or "cómo me llamo" in txt or "como me llamo" in txt:
            return f"Te llamas {user.get('name', 'amor')} 💜"

        # Ciudad
        if "mi ciudad" in txt or "dónde vivo" in txt or "donde vivo" in txt:
            return user.get("city", "No tengo tu ciudad guardada.")

        # Clima
        if "clima" in txt or "tiempo" in txt:
            if not weather.get("temp"):
                return "Aún no tengo clima sincronizado 💜"
            return (
                f"En {user.get('city','tu ciudad')} hay "
                f"{weather['temp']}°C y {weather['description']}."
            )


        # ============================================================
        # 10) FALLBACK — respuesta generada por AuriMind
        # ============================================================
        return raw_answer
