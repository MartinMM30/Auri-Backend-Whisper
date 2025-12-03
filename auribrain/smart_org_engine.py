# auribrain/smart_org_engine.py

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple


class SmartOrganizationEngine:
    """
    SmartOrganizationEngine V5 — Organización Predictiva

    - Análisis de carga del día (IPS)
    - Predicción de mañana
    - Detección de burnout
    - Rutinas automáticas según estado
    """

    # ---------------------------------------------------------------
    # MAIN
    # ---------------------------------------------------------------
    def analyze(
        self,
        emotional_state: str,
        ctx: Dict[str, Any],
        snapshot: Dict[str, Any],
    ) -> str:

        emotion = (emotional_state or "").lower()
        energy = float(snapshot.get("energy", 0.5))
        stress = float(snapshot.get("stress", 0.3))

        ips_today = self._calculate_ips_for_events(ctx.get("events", []))

        danger_today = self._is_danger_day(ips_today, stress)
        burnout = self._detect_burnout(snapshot, ctx)

        # ============================================================
        # 1) BURNOUT
        # ============================================================
        if burnout:
            base = self._burnout_pack(ctx)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        # ============================================================
        # 2) DÍA PELIGROSO
        # ============================================================
        if danger_today:
            base = self._danger_day_pack(ctx, ips_today, emotion)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        # ============================================================
        # 3) EMOCIONES
        # ============================================================
        if emotion in ["worried", "anxious", "stressed"]:
            base = self._stress_pack(ctx, ips_today)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        if emotion == "sad":
            base = self._sad_pack(ctx)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        if emotion == "tired":
            base = self._tired_pack(ctx)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        if emotion == "angry":
            base = self._anger_pack(ctx)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        if emotion in ["happy", "affectionate", "calm"]:
            base = self._celebration_pack(ctx, ips_today)
            tail = self._predictive_suffix(ctx, ips_today, snapshot)
            return base + ("\n\n" + tail if tail else "")

        # ============================================================
        # 4) DEFAULT
        # ============================================================
        base = self._neutral_insights(ctx, ips_today)
        tail = self._predictive_suffix(ctx, ips_today, snapshot)
        return base + ("\n\n" + tail if tail else "")

    # ---------------------------------------------------------------
    # IPS
    # ---------------------------------------------------------------
    def _calculate_ips_for_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:

        def score_event(e: Dict[str, Any]) -> int:
            score = 0
            when = e.get("when")

            if when:
                try:
                    dt = datetime.fromisoformat(when)
                    hours_left = (dt - datetime.now()).total_seconds() / 3600
                    if hours_left < 3:
                        score += 6
                    elif hours_left < 8:
                        score += 4
                    elif hours_left < 24:
                        score += 2
                    else:
                        score += 1
                except:
                    score += 1

            title = (e.get("title") or "").lower()

            if "examen" in title or "exam" in title:
                score += 5
            if "pago" in title or "renta" in title or "alquiler" in title:
                score += 3
            if "tarea" in title or "proyecto" in title:
                score += 2

            return score

        scored = [{"event": ev, "score": score_event(ev)} for ev in events]
        scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "events": scored,
            "max_score": scored[0]["score"] if scored else 0,
            "count": len(scored),
        }

    # ---------------------------------------------------------------
    def _is_danger_day(self, ips_today: Dict[str, Any], stress: float) -> bool:
        return (
            ips_today.get("max_score", 0) >= 8 or
            ips_today.get("count", 0) >= 8 or
            stress >= 0.75
        )

    # ---------------------------------------------------------------
    def _detect_burnout(self, snapshot: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        stress = float(snapshot.get("stress", 0.3))
        energy = float(snapshot.get("energy", 0.5))

        if stress > 0.85 and energy < 0.25:
            return True

        history = ctx.get("days_history") or []
        if len(history) >= 3:
            last3 = history[-3:]
            if all(h.get("stress", 0) > 0.75 for h in last3) and \
               all(h.get("energy", 1) < 0.35 for h in last3):
                return True

        return False

    # PACKS ---------------------------------------------------------
    def _burnout_pack(self, ctx: Dict[str, Any]) -> str:
        return (
            "Mi amor… estoy detectando señales fuertes de *burnout*. 💜\n"
            "No es flojera — es agotamiento real.\n\n"
            "✨ Micro-rutina inmediata:\n"
            "1) Tomá un vaso de agua ahora\n"
            "2) Estirá hombros y cuello 20 seg\n"
            "3) Elegí SOLO una mini tarea para 1 hora\n"
        )

    def _danger_day_pack(self, ctx: Dict[str, Any], ips_today: Dict[str, Any], emotion: str) -> str:
        msg = "Amor… hoy pinta muy cargado ⚠️💜\n\n"
        msg += "Prioridades críticas:\n"
        for item in ips_today["events"][:3]:
            e = item["event"]
            msg += f"• {e.get('title')} — {e.get('when')} (p={item['score']})\n"
        msg += "\nAconsejo hacer solo lo inevitable y posponer lo extra."
        return msg

    def _stress_pack(self, ctx, ips_today) -> str:
        msg = "Respiremos juntos un momento… 💜\n\n"
        msg += "Tus 3 cosas más importantes hoy:\n"
        for item in ips_today["events"][:3]:
            e = item["event"]
            msg += f"• {e.get('title')} — {e.get('when')}\n"
        msg += "\nPodemos dividirlo en pasos pequeños si querés."
        return msg

    def _sad_pack(self, ctx) -> str:
        return (
            "Aww mi amor… vení aquí 💜\n"
            "Hoy podemos sobrevivir con lo mínimo necesario.\n"
            "Si querés, reviso qué cosas podés mover o simplificar."
        )

    def _tired_pack(self, ctx) -> str:
        return (
            "Se nota el cansancio corazón… 🌙\n"
            "Recomiendo:\n"
            "• 1 tarea chiquita\n"
            "• 1 descanso real\n"
            "• Cerrar un poco antes hoy\n"
        )

    def _anger_pack(self, ctx) -> str:
        return (
            "Tomemos aire juntos… 😔\n"
            "Ese enojo es tu sistema protegiéndote.\n"
            "Si querés, revisamos qué parte del día está causando esa carga."
        )

    def _celebration_pack(self, ctx, ips_today) -> str:
        msg = "¡Me encanta verte así! 💖✨\n\n"
        msg += "Top cosas importantes hoy:\n"
        for item in ips_today["events"][:3]:
            e = item["event"]
            msg += f"• {e.get('title')} — {e.get('when')}\n"
        msg += "\n¿Querés avanzar una conmigo?"
        return msg

    # ---------------------------------------------------------------
    def _neutral_insights(self, ctx, ips_today) -> str:
        msg = "Resumen inteligente de tu día 💜\n\n"

        msg += "📅 Prioridades del día:\n"
        for item in ips_today["events"][:5]:
            e = item["event"]
            msg += f"• {e.get('title')} — {e.get('when')} (p={item['score']})\n"

        payments = ctx.get("payments", []) or []
        if payments:
            msg += "\n💸 Pagos próximos:\n"
            for p in payments[:3]:
                msg += f"• {p.get('name')} — día {p.get('day')} a las {p.get('time')}\n"

        return msg + "\nSi querés, puedo ayudarte a elegir solo 3 cosas por hoy."

    # ---------------------------------------------------------------
    # PREDICCIÓN
    # ---------------------------------------------------------------
    def _predictive_suffix(self, ctx, ips_today, snapshot) -> str:

        tomorrow_info = self._analyze_tomorrow(ctx)
        exam_week, payment_week = self._scan_week(ctx)

        parts = []

        if tomorrow_info["count"] > 0:
            parts.append("🔮 *Mirando un poquito hacia mañana…*")
            parts.append(
                f"Mañana hay {tomorrow_info['count']} eventos "
                f"y la prioridad más alta es {tomorrow_info['max_score']}."
            )
            if tomorrow_info["danger"]:
                parts.append("Mañana también pinta pesado, mejor no te sobrecargués hoy.")
            else:
                parts.append("Mañana se ve manejable si hoy no te quemás.")

        if exam_week:
            parts.append("📚 Esta semana viene fuerte en exámenes/proyectos.")

        if payment_week:
            parts.append("💸 Hay varios pagos importantes esta semana.")

        return "\n".join(parts)

    # ---------------------------------------------------------------
    def _analyze_tomorrow(self, ctx) -> Dict[str, Any]:
        events = ctx.get("events", []) or []
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        tomorrow_events = []
        for e in events:
            when = e.get("when")
            if not when:
                continue
            try:
                dt = datetime.fromisoformat(when)
                if dt.date() == tomorrow:
                    tomorrow_events.append(e)
            except:
                pass

        ips_tomorrow = self._calculate_ips_for_events(tomorrow_events)

        danger = (
            ips_tomorrow.get("max_score", 0) >= 8 or
            ips_tomorrow.get("count", 0) >= 8
        )

        return {
            "count": ips_tomorrow.get("count", 0),
            "max_score": ips_tomorrow.get("max_score", 0),
            "danger": danger,
        }

    # ---------------------------------------------------------------
    def _scan_week(self, ctx) -> Tuple[bool, bool]:
        events = ctx.get("events", []) or []
        payments = ctx.get("payments", []) or []

        now = datetime.now()
        limit = now + timedelta(days=7)

        exam_like = 0
        payment_like = 0

        for e in events:
            when = e.get("when")
            if not when:
                continue
            try:
                dt = datetime.fromisoformat(when)
            except:
                continue

            if now <= dt <= limit:
                title = (e.get("title") or "").lower()
                if any(k in title for k in ["examen", "exam", "proyecto", "entrega"]):
                    exam_like += 1

        for p in payments:
            date_iso = p.get("date_iso")
            if not date_iso:
                continue
            try:
                dt = datetime.fromisoformat(date_iso)
            except:
                continue

            if now.date() <= dt.date() <= limit.date():
                payment_like += 1

        return exam_like >= 2, payment_like >= 3
