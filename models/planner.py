from pydantic import BaseModel, Field
from typing import Literal

class PlannerConfig(BaseModel):
    """
    Pydantic model representing the Planner's configuration.
    """
    mode: Literal["fast", "fast_listen_override", "smart"] = Field(
        default="fast",
        description="Planner execution mode."
    )
    schema_data: str = Field(
        default="{}",
        description="JSON describing the planner's field definitions (top-level only, no nesting)."
    )
    relevance_threshold: int = Field(
        default=50,
        description="Threshold (0-100) controlling tool routing likelihood. Higher values make routing to tools less likely."
    )