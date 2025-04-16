# app/models/user.py

from pydantic import BaseModel, Field

class UserConfig(BaseModel):
    """
    Pydantic model representing the User's configuration.

    This might align with the planner fields (e.g., 'customerType', 'region')
    plus an 'other_context' field, or anything else the admin wants to store.
    """
    user_json: str = Field(
        default="{}",
        description=(
            "A JSON string representing the user data. "
            "Should ideally match the planner schema (e.g. 'customerType', 'region'), "
            "plus an 'other_context' field for additional context."
        )
    )
