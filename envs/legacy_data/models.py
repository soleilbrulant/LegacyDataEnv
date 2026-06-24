from typing import Literal, Optional, List, Dict, Any
from pydantic import Field

# Bug Fix #1: Correct import path for openenv-core v0.3.0
# The types live in openenv.core.env_server.types, not at the top-level env_server module
from openenv.core.env_server.types import Action, Observation, State


class LegacyAction(Action):
    """The AI has exactly two buttons it can press."""

    action_type: Literal["execute_sql", "submit_solution"]

    # If it presses execute_sql, it must provide this string.
    sql_query: Optional[str] = Field(
        None,
        description="The exact SQL query to run against the legacy database.",
    )

    # If it presses submit_solution, it provides its final answer here.
    answer: Optional[str] = Field(
        None,
        description="Final answer or explanation to submit for grading.",
    )


class LegacyObservation(Observation):
    """Standard response format.

    Note: `done` and `reward` are inherited from Observation base class.
    We only add our custom fields here.
    """

    success: bool = Field(default=True, description="Whether the action succeeded.")
    data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Result set from a successful SELECT query.",
    )
    error_message: Optional[str] = Field(
        None,
        description="Raw SQL engine errors if the query fails.",
    )
    feedback: Optional[str] = Field(
        None,
        description="General environment feedback or grader output.",
    )


class LegacyState(State):
    """Internal state tracked across steps."""

    task_level: str = Field(default="easy", description="Current task level.")