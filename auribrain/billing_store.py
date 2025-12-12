from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auribrain.billing_utils import apply_plan_to_user, VALID_PLANS

router = APIRouter(prefix="/billing/store", tags=["billing_store"])


class StoreVerificationRequest(BaseModel):
    uid: str
    platform: str   # "ios" | "android"
    plan: str       # "pro" | "ultra"
    receipt: str    # token / recibo crudo


@router.post("/verify")
async def verify_store_purchase(body: StoreVerificationRequest):
    uid = body.uid
    platform = body.platform.lower()
    plan = body.plan.lower()
    receipt = body.receipt

    if plan not in VALID_PLANS or plan == "free":
        raise HTTPException(status_code=400, detail="Plan inválido")

    if platform not in ("ios", "android"):
        raise HTTPException(status_code=400, detail="Plataforma inválida")

    if not receipt:
        raise HTTPException(status_code=400, detail="Recibo/Token vacío")

    # Aquí debería ir la verificación REAL:
    is_valid = False
    subscription_id = None

    if platform == "ios":
        # TODO:
        # 1) Llamar App Store Server API con el recibo
        # 2) Validar estado de la suscripción
        # 3) Extraer subscription_id
        #
        # Ejemplo conceptual:
        # result = verify_with_apple(receipt)
        # is_valid = result["active"]
        # subscription_id = result["subscription_id"]
        pass

    elif platform == "android":
        # TODO:
        # 1) Llamar Google Play Developer API (purchases.subscriptions)
        # 2) Validar purchaseToken
        # 3) Extraer subscription_id
        #
        # Ejemplo conceptual:
        # result = verify_with_google(receipt)
        # is_valid = result["active"]
        # subscription_id = result["subscription_id"]
        pass

    # 🔥 mientras estás desarrollando y probando UI puedes dejarlo forzado:
    # ⚠ QUÍTALO para producción
    is_valid = True

    if not is_valid:
        raise HTTPException(status_code=400, detail="La suscripción no es válida / no está activa")

    apply_plan_to_user(
        uid=uid,
        plan=plan,
        provider=platform,
        subscription_id=subscription_id,
        status="active",
    )

    return {"ok": True, "plan": plan}
