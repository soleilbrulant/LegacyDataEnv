from typing import Literal, Optional, List, Dict, Any
from pydantic import Field
from openenv.core.env_server import Action, Observation

class LegacyAction(Action):
    # The AI has exactly two buttons it can press.
    action_type: Literal["execute_sql", "submit_solution"]
    
    # If it presses execute_sql, it must provide this string.
    sql_query: Optional[str] = Field(None, description="The exact SQL query to run against the legacy database.")
    
    # If it presses submit_solution, it provides its final answer here.
    answer: Optional[str] = Field(None, description="Final answer or explanation to submit for grading.")

class LegacyObservation(Observation):
    # Our standard response format
    success: bool
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Result set from a successful SELECT query.")
    error_message: Optional[str] = Field(None, description="Raw SQL engine errors if the query fails.")
    feedback: Optional[str] = Field(None, description="General environment feedback or grader output.")