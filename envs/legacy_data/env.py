import sqlite3
from typing import Any
from openenv.core.env_server import State
from openenv.core.client_types import StepResult
from .models import LegacyAction, LegacyObservation

class LegacyDataEnvironment:
    def __init__(self):
        self.db_path = ":memory:"
        self.conn = None
        self.step_count = 0
        self.task_level = "easy"
        self.episode_id = "legacy-eval-001"

    def _setup_legacy_db(self):
        """Phase 1 Sandbox code injected directly into the engine."""
        cursor = self.conn.cursor()
        
        # Easy Task Data
        cursor.execute("CREATE TABLE usr_accnts (id INTEGER PRIMARY KEY, username TEXT, balance_str TEXT)")
        cursor.executemany("INSERT INTO usr_accnts (username, balance_str) VALUES (?, ?)", 
                           [('alice_99', '$1500.50'), ('bob_smith', '€2450.00'), ('charlie_x', '£89.99'), ('david_d', '$3450.75')])
        
        # Medium Task Data
        cursor.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, item_name TEXT, stock_count INTEGER)")
        cursor.executemany("INSERT INTO inventory (item_name, stock_count) VALUES (?, ?)", 
                           [('MacBook Pro', 15), ('macbook pro', 42), ('Dell XPS', 8), ('dell xps', 2)])
        
        # Hard Task Data (Strict FKs enabled)
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO customers (name) VALUES ('Tech Corp'), ('Global Web')")
        cursor.execute("CREATE TABLE transactions (transaction_id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, FOREIGN KEY(customer_id) REFERENCES customers(customer_id))")
        cursor.execute("INSERT INTO transactions (transaction_id, customer_id, amount) VALUES (101, 1, 5000.0), (102, 2, 300.5)")
        
        self.conn.commit()

    def reset(self, task_level: str = "easy") -> LegacyObservation:
        """The Big Red Button. Wipes memory and rebuilds the dirty database."""
        self.task_level = task_level
        self.step_count = 0
        
        if self.conn:
            self.conn.close()
            
        self.conn = sqlite3.connect(self.db_path)
        self._setup_legacy_db()
        
        return LegacyObservation(
            success=True, 
            feedback=f"Legacy DB connected. Task level: {task_level}. You may begin executing SQL."
        )

    def step(self, action: LegacyAction) -> StepResult:
        """The core loop. Executes AI actions safely."""
        self.step_count += 1
        
        if action.action_type == "execute_sql":
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;") 
                cursor.execute(action.sql_query)
                
                if action.sql_query.strip().upper().startswith("SELECT"):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.conn.commit()
                    data = []
                    
                obs = LegacyObservation(success=True, data=data)
                return StepResult(observation=obs, reward=0.0, done=False)
                
            except sqlite3.Error as e:
                obs = LegacyObservation(success=False, error_message=f"SQL Engine Error: {str(e)}")
                return StepResult(observation=obs, reward=0.0, done=False)
                
        elif action.action_type == "submit_solution":
            reward = self._grade_task(action.answer)
            obs = LegacyObservation(success=True, feedback=f"Episode terminated. Final Score: {reward}")
            return StepResult(observation=obs, reward=reward, done=True)

    def state(self) -> State:
        return State(episode_id=self.episode_id, step_count=self.step_count)

    def _grade_task(self, answer: str) -> float:
        """Evaluates the database state and assigns a score from 0.0 to 1.0"""
        cursor = self.conn.cursor()
        score = 0.0

        try:
            # --- EASY TASK: Reconnaissance ---
            if self.task_level == "easy":
                # The highest balance is David D ($3450.75). We check the agent's submitted string.
                if answer and ("3450.75" in answer or "3450" in answer):
                    return 1.0
                return 0.0

            # --- MEDIUM TASK: Data Rescue ---
            elif self.task_level == "medium":
                cursor.execute("SELECT COUNT(*) FROM inventory;")
                total_rows = cursor.fetchone()[0]
                
                if total_rows == 4:
                    return 0.0 # Agent did nothing
                
                if total_rows == 2:
                    score += 0.5 # 50% partial credit for reducing rows to 2
                    
                    # Did they keep the right ones? (macbook pro: 42, Dell XPS: 8. Total = 50)
                    cursor.execute("SELECT SUM(stock_count) FROM inventory;")
                    total_stock = cursor.fetchone()[0]
                    if total_stock == 50:
                        score += 0.5 # 100% credit!
                return score

            # --- HARD TASK: Schema Migration ---
            elif self.task_level == "hard":
                # 1. Did the table survive the migration?
                cursor.execute("PRAGMA table_info(transactions);")
                columns = cursor.fetchall()
                
                # 2. Did they successfully change transaction_id to a text-based UUID field?
                for col in columns:
                    if col[1] == 'transaction_id':
                        if 'TEXT' in col[2].upper() or 'VARCHAR' in col[2].upper():
                            score += 0.5 # 50% partial credit for the schema change
                
                # 3. Did the original data survive the migration without violating foreign keys?
                cursor.execute("SELECT COUNT(*) FROM transactions;")
                if cursor.fetchone()[0] == 2:
                    score += 0.5 # 100% credit!
                    
                return score
                
        except sqlite3.Error:
            # If the agent corrupted the DB so badly that our grader queries fail, they get a 0.
            return 0.0
            
        return score