from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, Dict, List
from datetime import datetime
import uuid
from .contract import SharedContract
from .kill_report import KillReport


class LogEntry(BaseModel):
    timestamp: str
    agent: str
    message: str
    level: Literal["INFO", "WARNING", "CRITICAL", "SUCCESS"]


class Mission(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    input_prompt: str
    status: Literal["PENDING", "GENESIS", "CONSTRUCTION", "ATTACK", "DEFENSE", "DEPLOYING", "DEPLOYED", "FAILED"] = "PENDING"
    current_phase: str = "Initializing"
    contract: Optional[SharedContract] = None
    generated_files: Dict[str, str] = Field(default_factory=dict)
    kill_reports: List[KillReport] = Field(default_factory=list)
    survival_score: float = 100.0
    deploy_url: Optional[str] = None
    combat_log: List[LogEntry] = Field(default_factory=list)
    error: Optional[str] = None

    def add_log(self, agent: str, message: str, level: str = "INFO"):
        self.combat_log.append(LogEntry(
            timestamp=datetime.utcnow().strftime("%H:%M:%S"),
            agent=agent,
            message=message,
            level=level
        ))

    def recalculate_score(self):
        if not self.kill_reports:
            self.survival_score = 100.0
            return
        total = len(self.kill_reports)
        resolved = sum(1 for r in self.kill_reports if r.status in ["PATCHED", "DISMISSED"])
        base = (resolved / total) * 100
        critical_open = sum(1 for r in self.kill_reports if r.severity == "CRITICAL" and r.status == "OPEN")
        penalty = critical_open * 15
        self.survival_score = max(0.0, min(100.0, base - penalty))
