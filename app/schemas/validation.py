from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class ValidationRequest(BaseModel):
    components: Dict[str, str] = Field(..., description="Component type -> product ID mapping")
    # Example: {"cpu": "uuid", "motherboard": "uuid", "gpu": "uuid", ...}


class ValidationIssue(BaseModel):
    component_type: str
    issue_type: str  # compatibility, power, form_factor, etc.
    severity: str  # error, warning
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    total_power_consumption: Optional[float] = None
    recommended_psu_wattage: Optional[float] = None
    performance_score: Optional[float] = None

