from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List, Any


class Feature(BaseModel):
    id: str = Field(description="Unique feature ID like feat_001")
    name: str
    description: str
    priority: Literal["P0", "P1", "P2"]
    user_story: str = Field(description="As a [user], I want to [action] so that [benefit]")


class UserJourney(BaseModel):
    persona: str
    steps: List[str]
    success_condition: str


class Column(BaseModel):
    name: str
    sql_type: str = Field(
        description="Real SQL type: UUID, VARCHAR(255), DECIMAL(10,2), TIMESTAMPTZ, JSONB, BOOLEAN, INTEGER, TEXT"
    )
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    index: bool = False


class Table(BaseModel):
    name: str
    columns: List[Column]
    relationships: List[str] = Field(default_factory=list)


class Endpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    description: str
    auth_required: bool
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None


class TechStack(BaseModel):
    frontend: str
    backend: str
    database: str
    auth: str
    hosting: str


class PricingTier(BaseModel):
    name: str
    price_monthly_usd: float
    price_annual_usd: float
    features: List[str]
    target_segment: str


class Amendment(BaseModel):
    timestamp: str
    agent: str
    field_changed: str
    reason: str
    new_value: str


class SharedContract(BaseModel):
    company_name: str
    tagline: str
    problem_statement: str
    target_users: List[str]
    core_features: List[Feature]
    user_journeys: List[UserJourney]
    tech_stack: TechStack
    database_schema: List[Table]
    api_endpoints: List[Endpoint]
    pricing_tiers: List[PricingTier]
    revenue_model: str
    go_to_market: str
    compliance_requirements: List[str]
    known_risks: List[str]
    amendments: List[Amendment] = Field(default_factory=list)
    version: int = 1
