import os
import stripe
import firebase_admin
from firebase_admin import auth, firestore
from fastapi import APIRouter, Request, HTTPException
from auribrain.auri_singleton import auri

router = APIRouter()

# =========================
# STRIPE CONFIG
# =========================
stripe.api_key = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

PRICE_PRO = os.getenv("STRIPE_PRICE_PRO")        # p.ej price_123
PRICE_ULTRA = os.getenv("STRIPE_PRICE_ULTRA")    # p.ej price_456

# =========================
# FIREBASE ADMIN (ya inicializado antes)
# =========================
db = firestore.client()


# ===========================================================
#       📌 Utilidad para actualizar plan en Firebase
# ===========================================================
def update_user_plan(uid: str, plan: str):
    print(f"🔥 Actualizando plan para UID={uid}: {plan}")

    # → 1. CUSTOM CLAIMS
    try:
        auth.set_custom_user_claims(uid, {"plan": plan})
    except Exception as e:
        print("❌ Error actualizando claims:", e)

    # → 2. FIRESTORE (tabla users)
    try:
        db.collection("users").document(uid).set({"plan": plan}, merge=True)
    except Exception as e:
        print("❌ Error guardando en Firestore:", e)

    # → 3. AURI CONTEXT ENGINE
    try:
        auri.context.set_user_plan(plan)
    except Exception as e:
        print("❌ Error AuriMind:", e)


# ===========================================================
#       📌 ENDPOINT WEBHOOK OFICIAL
# ===========================================================
@router.post("/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # 1. VALIDAR FIRMA
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    print("📥 Evento Stripe recibido:", event["type"])

    # ======================================
    #  EVENTOS QUE NOS IMPORTAN
    # ======================================

    # ---------------------------
    # SUSCRIPCIÓN CREADA / ACTIVA
    # ---------------------------
    if event["type"] == "customer.subscription.created" or \
       event["type"] == "customer.subscription.updated":

        sub = event["data"]["object"]
        uid = sub["metadata"].get("firebase_uid") if "metadata" in sub else None

        if not uid:
            print("⚠ Suscripción sin UID, ignorada")
            return {"ok": True}

        price_id = sub["items"]["data"][0]["price"]["id"]

        # PRO
        if price_id == PRICE_PRO:
            update_user_plan(uid, "pro")

        # ULTRA
        elif price_id == PRICE_ULTRA:
            update_user_plan(uid, "ultra")

        # FREE fallback
        else:
            update_user_plan(uid, "free")

        return {"ok": True}

    # ---------------------------
    # CANCELACIÓN
    # ---------------------------
    if event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        uid = sub["metadata"].get("firebase_uid")

        if uid:
            update_user_plan(uid, "free")

        return {"ok": True}

    return {"received": True}
