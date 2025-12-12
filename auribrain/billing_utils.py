# auribrain/billing_utils.py

from typing import Optional, Dict
import firebase_admin
from firebase_admin import auth, firestore

VALID_PLANS = {"free", "pro", "ultra"}

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()


def apply_plan_to_user(
    uid: str,
    plan: str,
    provider: str,
    subscription_id: Optional[str] = None,
    status: str = "active",
    extra: Optional[Dict] = None,
):
    """
    Aplica un plan a un usuario:
    - Actualiza Firestore: users/{uid}.plan
    - Actualiza billing.{provider, status, subscription_id}
    - Actualiza custom claims: { plan: ... }
    """

    if not uid:
        raise ValueError("UID requerido")

    plan = (plan or "").lower().strip()
    if plan not in VALID_PLANS:
        plan = "free"

    provider = (provider or "unknown").lower().strip()

    billing_data = {
        "provider": provider,
        "status": status,
    }
    if subscription_id:
        billing_data["subscription_id"] = subscription_id

    if extra:
        billing_data.update(extra)

    # 1) Firestore
    db.collection("users").document(uid).set(
        {
            "plan": plan,
            "billing": billing_data,
        },
        merge=True,
    )

    # 2) Custom claims
    # Ojo: esto sobreescribe claims anteriores, si quieres combinarlos
    # podrías primero leer claims anteriores y actualizarlos.
    auth.set_custom_user_claims(uid, {"plan": plan})

    print(f"[Billing] Plan '{plan}' aplicado a uid={uid} via {provider}")
