from fastapi import APIRouter
from auribrain.subscription.service import get_subscription, set_subscription

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/status")
def status(uid: str):
    return get_subscription(uid)

@router.post("/set")
def set_plan(uid: str, plan: str):
    return set_subscription(uid, plan)
