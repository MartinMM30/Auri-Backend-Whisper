# por ahora memoria / mongo / redis
# luego Stripe escribe aquí

_FAKE_DB = {}

def get_subscription(uid: str) -> dict:
    sub = _FAKE_DB.get(uid)
    if not sub:
        return {
            "plan": "free",
            "active": False,
            "provider": "debug",
            "expires_at": None,
        }
    return sub


def set_subscription(uid: str, plan: str):
    _FAKE_DB[uid] = {
        "plan": plan,
        "active": plan != "free",
        "provider": "debug",
        "expires_at": None,
    }
    return _FAKE_DB[uid]
