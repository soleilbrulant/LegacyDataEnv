import sqlite3
from typing import Any, Optional
from uuid import uuid4

# Bug Fix #2: Import the Environment abstract base class and proper types
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from .models import LegacyAction, LegacyObservation, LegacyState


# --- THE ENGINE ---
# Bug Fix #3: Extend Environment[Action, Observation, State] instead of plain class
# Bug Fix #4: Implementing the required abstract `state` property
class LegacyDataEnvironment(Environment[LegacyAction, LegacyObservation, LegacyState]):
    """
    An advanced, real-world OpenEnv environment simulating a chaotic, 10-year-old
    legacy SQLite database. Designed to test an AI agent's ability to act as a
    backend reliability engineer.

    Tasks:
      - Easy:   Extract max values from columns contaminated with mixed currency symbols.
      - Medium: Case-insensitive deduplication retaining rows with max stock_count.
      - Hard:   Migrate integer PK to TEXT UUID without violating FK constraints.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        super().__init__()
        self.db_path = ":memory:"
        self.conn: Optional[sqlite3.Connection] = None
        self._state = LegacyState(
            episode_id=str(uuid4()),
            step_count=0,
            task_level="easy",
        )
        # Auto-initialize DB so the environment is ready immediately
        # check_same_thread=False is required because uvicorn runs sync code in a
        # thread pool executor — the connection must be usable across threads
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._setup_legacy_db()

    # ------------------------------------------------------------------
    # Bug Fix #4: Implement the abstract `state` property
    # ------------------------------------------------------------------
    @property
    def state(self) -> LegacyState:
        return self._state

    # ------------------------------------------------------------------
    # Internal DB setup
    # ------------------------------------------------------------------
    def _setup_legacy_db(self) -> None:
        cursor = self.conn.cursor()

        # Easy task table — balance contaminated with currency symbols
        cursor.execute(
            "CREATE TABLE usr_accnts (id INTEGER PRIMARY KEY, username TEXT, balance_str TEXT)"
        )
        cursor.executemany(
            "INSERT INTO usr_accnts (username, balance_str) VALUES (?, ?)",
            [
                ("alice_99", "$1500.50"),
                ("bob_smith", "€2450.00"),
                ("charlie_x", "£89.99"),
                ("david_d", "$3450.75"),
            ],
        )

        # Medium task table — duplicates with different cases
        cursor.execute(
            "CREATE TABLE inventory (id INTEGER PRIMARY KEY, item_name TEXT, stock_count INTEGER)"
        )
        cursor.executemany(
            "INSERT INTO inventory (item_name, stock_count) VALUES (?, ?)",
            [
                ("MacBook Pro", 15),
                ("macbook pro", 42),
                ("Dell XPS", 8),
                ("dell xps", 2),
            ],
        )

        # Hard task tables — FK relationship with integer PK to be migrated to TEXT
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(
            "CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT)"
        )
        cursor.execute(
            "INSERT INTO customers (name) VALUES ('Tech Corp'), ('Global Web')"
        )
        cursor.execute(
            """CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                amount REAL,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            )"""
        )
        cursor.execute(
            "INSERT INTO transactions (transaction_id, customer_id, amount) "
            "VALUES (101, 1, 5000.0), (102, 2, 300.5)"
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Bug Fix: reset() signature matches Environment base class
    # ------------------------------------------------------------------
    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> LegacyObservation:
        """Reset the environment. Accepts task_level in kwargs."""
        task_level = kwargs.get("task_level", "easy")

        self._state = LegacyState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_level=task_level,
        )

        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._setup_legacy_db()

        return LegacyObservation(
            success=True,
            feedback=f"Connected. Level: {task_level}. DB ready.",
            done=False,
            reward=0.0,
        )

    # ------------------------------------------------------------------
    # Bug Fix #2: step() returns LegacyObservation (not StepResult)
    # Bug Fix: step() signature matches Environment base class
    # ------------------------------------------------------------------
    def step(
        self,
        action: LegacyAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> LegacyObservation:
        """Execute a step. action_type can be 'execute_sql' or 'submit_solution'."""
        self._state.step_count += 1

        # Handle both Pydantic models and raw dicts (for HTTP deserialization)
        if isinstance(action, dict):
            action = LegacyAction(**action)

        action_type = action.action_type
        sql_query = action.sql_query or ""
        answer = action.answer or ""

        if action_type == "execute_sql":
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(sql_query)
                if sql_query.strip().upper().startswith("SELECT"):
                    columns = (
                        [col[0] for col in cursor.description]
                        if cursor.description
                        else []
                    )
                    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.conn.commit()
                    data = []
                return LegacyObservation(
                    success=True,
                    data=data,
                    done=False,
                    reward=0.01,
                )
            except Exception as e:
                return LegacyObservation(
                    success=False,
                    error_message=str(e),
                    done=False,
                    reward=0.0,
                )

        elif action_type == "submit_solution":
            # Bug Fix #6: reward ceiling raised to 1.0 so success=true is possible
            reward = self._grade_task(answer)
            return LegacyObservation(
                success=True,
                feedback=f"Graded. Score: {reward:.2f}",
                done=True,
                reward=reward,
            )

        return LegacyObservation(
            success=False,
            error_message="Invalid action_type. Use 'execute_sql' or 'submit_solution'.",
            done=False,
            reward=0.0,
        )

    # ------------------------------------------------------------------
    # Grader — Bug Fix #6: returns 1.0 (not 0.99) so success check passes
    # ------------------------------------------------------------------
    def _grade_task(self, answer: str) -> float:
        cursor = self.conn.cursor()
        try:
            if self._state.task_level == "easy":
                # Agent must identify that 3450.75 is the max numeric value
                return 1.0 if answer and ("3450.75" in answer) else 0.0

            elif self._state.task_level == "medium":
                # After dedup: 2 canonical rows (MacBook Pro=42, Dell XPS=8) → sum=50
                cursor.execute("SELECT COUNT(*) FROM inventory;")
                rows = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(stock_count) FROM inventory;")
                stock = cursor.fetchone()[0]
                if rows == 2 and stock == 50:
                    return 1.0
                elif rows == 2:
                    return 0.5
                else:
                    return 0.0

            elif self._state.task_level == "hard":
                # Check transaction_id column is now TEXT, and both rows still exist
                cursor.execute("PRAGMA table_info(transactions);")
                cols = cursor.fetchall()
                type_ok = any(
                    "TEXT" in c[2].upper() for c in cols if c[1] == "transaction_id"
                )
                cursor.execute("SELECT COUNT(*) FROM transactions;")
                count_ok = cursor.fetchone()[0] == 2
                if type_ok and count_ok:
                    return 1.0
                elif type_ok:
                    return 0.5
                else:
                    return 0.0

        except Exception:
            return 0.0

        return 0.0
