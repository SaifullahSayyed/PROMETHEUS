from pydantic import BaseModel, Field
from typing import Literal, Optional
import uuid
class KillReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    critic_type: Literal["SECURITY", "PRODUCT", "COMPLIANCE", "SCALABILITY", "BUSINESS"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    title: str
    description: str
    affected_layer: Literal["CODE", "SPEC", "BUSINESS_MODEL", "COMPLIANCE", "ARCHITECTURE"]
    kill_potential: int = Field(ge=1, le=10)
    suggested_fix: str
    status: Literal["OPEN", "PATCHED", "CHALLENGED", "DISMISSED"] = "OPEN"
    patch_description: Optional[str] = None
    challenge_argument: Optional[str] = None
    arbiter_verdict: Optional[Literal["ACCEPTED", "REJECTED"]] = None