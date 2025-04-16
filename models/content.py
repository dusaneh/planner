# app/models/content.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class ContentItem(BaseModel):
    """
    Represents a single piece of content or knowledge base entry.

    Fields:
    - title: Short title or identifier
    - body: Main text content or answer
    - index_name: Which index this content belongs to
    - query_strings: Array of possible user queries that map to this content
    - user_fields_mapping: Mapping of user attributes this content applies to
    - tags: List of tags for categorization and filtering
    """
    title: str = Field("Untitled Content", description="A short title or identifier.")
    body: str = Field("", description="Main text or answer for this content item.")
    index_name: str = Field("", description="Index name to which this content belongs.")
    query_strings: List[str] = Field(
        default_factory=list,
        description="List of user query variations that should retrieve this content."
    )
    user_fields_mapping: Dict[str, Union[str, List[str]]] = Field(
        default_factory=dict,
        description="Mapping of user attributes this content applies to (e.g., region, customerType)."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tags for categorizing and filtering content."
    )

class ContentConfig(BaseModel):
    """
    Pydantic model for the entire content configuration file,
    which may contain multiple content items.
    """
    items: List[ContentItem] = Field(
        default_factory=list,
        description="Array of content items in the knowledge base."
    )