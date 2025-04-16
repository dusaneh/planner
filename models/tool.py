# app/models/tool.py

from pydantic import BaseModel, Field, validator
from typing import Literal, Dict, List, Union

class ToolData(BaseModel):
    """
    Represents a single tool's configuration.

    Fields:
    - name: A short identifier for the tool
    - description: What the tool does
    - priority: Lower means the tool runs exclusively if chosen, same priority -> parallel
    - display_mode: 'as-is' or 'summarizable'
    - index_name: If set, this is a retrieval tool referencing that index
    - top_k: How many documents to retrieve initially
    - reranker: Which reranker strategy (mutually exclusive)
    - parameters_json: JSON array describing tool parameters
    - user_fields_mapping: Dict mapping each user field to specific values for filtering
    - disambiguation_level: 0..10 slider controlling how aggressively the tool clarifies user queries
    - can_be_overridden_when_sticky: If false, the tool won't be overridden in 'fast_listen_override'
    """

    name: str = Field("Untitled Tool", description="A short identifier for the tool.")
    description: str = Field("No description", description="Human-readable explanation of the tool's purpose.")
    priority: int = Field(100, description="Lower = exclusive if chosen; same priority = parallel with others.")
    display_mode: Literal["as-is", "summarizable"] = Field(
        default="as-is",
        description="Whether to display output verbatim or summarize it."
    )
    index_name: str = Field(
        "",
        description="If non-empty, this tool performs retrieval from the specified index."
    )
    top_k: int = Field(
        1,
        description="Number of documents to retrieve initially for a retrieval tool."
    )
    reranker: Literal["top1", "top3", "uprank_sdr"] = Field(
        default="top1",
        description="Mutually exclusive reranker option."
    )
    parameters_json: str = Field(
        "[]",
        description=(
            "JSON array describing the tool's parameters, e.g. "
            "[{\"name\": \"userId\", \"type\": \"string\", \"required\": true, \"description\": \"...\"}]."
        )
    )
    user_fields_mapping: Dict[str, Union[str, List[str]]] = Field(
        default_factory=dict,
        description=(
            "Dict mapping each user field to specific values for filtering. "
            "Values can be strings or lists of strings."
        )
    )
    disambiguation_level: int = Field(
        5,
        description="Slider from 0 (no clarifications) to 10 (always clarify if uncertain)."
    )
    can_be_overridden_when_sticky: bool = Field(
        True,
        description=(
            "If true, the 'fast_listen_override' mode can interrupt this tool's sticky session. "
            "If false, once the tool is active, it won't be overridden until it finishes."
        )
    )

    @validator("disambiguation_level")
    def check_disambiguation_range(cls, v):
        if not (0 <= v <= 10):
            raise ValueError("disambiguation_level must be between 0 and 10.")
        return v