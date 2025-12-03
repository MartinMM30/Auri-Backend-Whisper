# auribrain/voice_emotion_analyzer.py

import numpy as np

class VoiceEmotionAnalyzer:
    """
    VoiceEmotionAnalyzer V3.5 — con Debug Mode
    -------------------------------------------
    Analiza PCM 16-bit mono y produce etiquetas emocionales simples.
    Debug Mode permite ver internamente cómo se clasificó la voz.

    Emociones posibles:
    - happy
    - angry
    - tired
    - sad
    - neutral
    """

    def __init__(self, debug: bool = False):
        self.debug = debug

        # Thresholds calibrados
        self.THRESH_RMS_HAPPY = 0.25
        self.THRESH_RMS_ANGRY = 0.35
        self.THRESH_ZCR_ANGRY = 0.15
        self.THRESH_RMS_TIRED = 0.08
        self.THRESH_VAR_HAPPY = 0.015

    # -----------------------------------------------------------
    # 1) Conversión PCM → numpy array
    # -----------------------------------------------------------
    def _pcm_to_array(self, pcm: bytes):
        if not pcm:
            return np.array([], dtype=np.float32)

        arr = np.frombuffer(pcm, dtype=np.int16)
        if arr.size == 0:
            return np.array([], dtype=np.float32)

        return arr.astype(np.float32) / 32768.0

    # -----------------------------------------------------------
    # 2) Features acústicos
    # -----------------------------------------------------------
    def _rms(self, arr):
        return float(np.sqrt(np.mean(arr ** 2))) if len(arr) else 0.0

    def _zcr(self, arr):
        if len(arr) < 2:
            return 0.0
        zero_crossings = np.sum(np.abs(np.diff(np.sign(arr)))) / 2
        return float(zero_crossings / len(arr))

    def _variance(self, arr):
        return float(np.var(arr)) if len(arr) else 0.0

    # -----------------------------------------------------------
    # 3) Clasificación emocional
    # -----------------------------------------------------------
    def analyze(self, pcm_bytes: bytes):
        arr = self._pcm_to_array(pcm_bytes)

        if len(arr) == 0:
            return "neutral"

        rms = self._rms(arr)
        zcr = self._zcr(arr)
        var = self._variance(arr)

        # DEBUG MODE LOGGING
        if self.debug:
            print("\n================ AUDIO DEBUG ================")
            print(f"RMS:       {rms:.4f}")
            print(f"ZCR:       {zcr:.4f}")
            print(f"Variance:  {var:.4f}")

        # ---------------------------
        # Happiness
        # ---------------------------
        if rms > self.THRESH_RMS_HAPPY and var > self.THRESH_VAR_HAPPY:
            if self.debug:
                print("→ Clasificado como: HAPPY 🎉 (alta energía + alta variabilidad)")
            return "happy"

        # ---------------------------
        # Anger
        # ---------------------------
        if rms > self.THRESH_RMS_ANGRY and zcr > self.THRESH_ZCR_ANGRY:
            if self.debug:
                print("→ Clasificado como: ANGRY 😠 (mucha energía + mucha tensión)")
            return "angry"

        # ---------------------------
        # Tiredness
        # ---------------------------
        if rms < self.THRESH_RMS_TIRED:
            if self.debug:
                print("→ Clasificado como: TIRED 😴 (muy poca energía)")
            return "tired"

        # ---------------------------
        # Sadness
        # ---------------------------
        if rms < 0.12 and var < 0.008:
            if self.debug:
                print("→ Clasificado como: SAD 😢 (voz baja + poca variabilidad)")
            return "sad"

        # ---------------------------
        # Default
        # ---------------------------
        if self.debug:
            print("→ Clasificado como: NEUTRAL 😐")
            print("============================================\n")

        return "neutral"
