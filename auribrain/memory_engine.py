import json
import os
from datetime import datetime

class MemoryEngine:
    def __init__(self, save_file="auri_memory.json"):
        self.save_file = save_file

        self.short_term = []
        self.long_term = {}
        self.emotion_state = "neutral"
        self.narrative = []

        self._load()

    def add_interaction(self, text):
        self.short_term.append({
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        self.short_term = self.short_term[-24:]

        self._update_emotion(text)
        self._save()

    def get_recent(self):
        return [m["text"] for m in self.short_term[-12:]]

    def get_last(self, n=2):
        return [m["text"] for m in self.short_term[-n:]]

    def remember(self, key, value):
        self.long_term[key] = value
        self._save()

    def recall(self, key):
        return self.long_term.get(key)

    def get_profile(self):
        return self.long_term

    def _update_emotion(self, text):
        t = text.lower()
        if any(k in t for k in ["triste", "solo", "mal", "estresado"]):
            self.emotion_state = "sad"
        elif any(k in t for k in ["feliz", "contento", "motivado"]):
            self.emotion_state = "happy"
        elif any(k in t for k in ["cansado", "agotado"]):
            self.emotion_state = "tired"

    def get_emotion(self):
        return self.emotion_state

    def add_event(self, event):
        self.narrative.append({
            "event": event,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def get_narrative_summary(self):
        return [e["event"] for e in self.narrative[-10:]]

    def _save(self):
        try:
            data = {
                "short_term": self.short_term,
                "long_term": self.long_term,
                "emotion_state": self.emotion_state,
                "narrative": self.narrative
            }
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _load(self):
        if not os.path.exists(self.save_file):
            return
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.short_term = data.get("short_term", [])
            self.long_term = data.get("long_term", {})
            self.emotion_state = data.get("emotion_state", "neutral")
            self.narrative = data.get("narrative", [])
        except:
            pass
