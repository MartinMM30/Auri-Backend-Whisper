import os
from pymongo import MongoClient
from datetime import datetime
from typing import Optional

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["auri"]               # usa la misma DB que el resto del proyecto
subs = db["subscriptions"]        # colección nueva


def get_subscription(uid: str) -> dict:
    doc = subs.find_one({"uid": uid})

    if not doc:
        return {
            "plan": "free",
            "active": False,
            "provider": "debug",
            "expires_at": None,
        }

    return {
        "plan": doc.get("plan", "free"),
        "active": doc.get("active", False),
        "provider": doc.get("provider", "debug"),
        "expires_at": doc.get("expires_at"),
    }


def set_subscription(uid: str, plan: str):
    data = {
        "uid": uid,
        "plan": plan,
        "active": plan != "free",
        "provider": "debug",
        "expires_at": None,
        "updated_at": datetime.utcnow(),
    }

    subs.update_one(
        {"uid": uid},
        {"$set": data},
        upsert=True,
    )

    return data
