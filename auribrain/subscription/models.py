from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubscriptionStatus(BaseModel):
    plan: str  # free | pro | ultra
    active: bool
    provider: str  # debug | stripe | apple
    expires_at: Optional[datetime]
