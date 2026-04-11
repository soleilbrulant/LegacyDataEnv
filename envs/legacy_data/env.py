import sqlite3
from typing import Any, Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel

# Import the official OpenEnv types
from openenv.core.client_types import StepResult
from .models import LegacyObservation

# --- THE ENGINE ---
class LegacyDataEnvironment:
    def __init__(self):
        self.db_path = ":memory:"
        self.conn = None
        self.step_count = 0
        self.task_level = "easy"
        self.episode_id = "legacy-eval-001"

    def _setup_legacy_db(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE usr_accnts (id INTEGER PRIMARY KEY, username TEXT, balance_str TEXT)")
        cursor.executemany("INSERT INTO usr_accnts (username, balance_str) VALUES (?, ?)", 
                           [('alice_99', '$1500.50'), ('bob_smith', '€2450.00'), ('charlie_x', '£89.99'), ('david_d', '$3450.75')])
        cursor.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, item_name TEXT, stock_count INTEGER)")
        cursor.executemany("INSERT INTO inventory (item_name, stock_count) VALUES (?, ?)", 
                           [('MacBook Pro', 15), ('macbook pro', 42), ('Dell XPS', 8), ('dell xps', 2)])
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO customers (name) VALUES ('Tech Corp'), ('Global Web')")
        cursor.execute("CREATE TABLE transactions (transaction_id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, FOREIGN KEY(customer_id) REFERENCES customers(customer_id))")
        cursor.execute("INSERT INTO transactions (transaction_id, customer_id, amount) VALUES (101, 1, 5000.0), (102, 2, 300.5)")
        self.conn.commit()

    def reset(self, task_level: str = "easy"):
        self.task_level = task_level
        self.step_count = 0
        if self.conn: self.conn.close()
        self.conn = sqlite3.connect(self.db_path)
        self._setup_legacy_db()
        # Return an object for Phase 2
        return LegacyObservation(success=True, feedback=f"Connected. Level: {task_level}")

    def step(self, action_data):
        self.step_count += 1
        
        # Safely handle inputs (Pydantic models OR dicts)
        if hasattr(action_data, "dict"):
            action_dict = action_data.dict()
        elif hasattr(action_data, "model_dump"): 
            action_dict = action_data.model_dump()
        elif isinstance(action_data, dict):
            action_dict = action_data
        else:
            action_dict = {}
            
        action_type = action_dict.get("action_type")
        sql_query = action_dict.get("sql_query", "")
        answer = action_dict.get("answer", "")

        if action_type == "execute_sql":
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute(sql_query)
                if sql_query.strip().upper().startswith("SELECT"):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.conn.commit()
                    data = []
                obs = LegacyObservation(success=True, data=data)
                # Changed 0.0 to 0.01 for strict validation
                return StepResult(observation=obs, reward=0.01, done=False)
            except Exception as e:
                obs = LegacyObservation(success=False, error_message=str(e))
                return StepResult(observation=obs, reward=0.01, done=False)
        
        elif action_type == "submit_solution":
            reward = self._grade_task(answer)
            obs = LegacyObservation(success=True, feedback=f"Done. Score: {reward}")
            return StepResult(observation=obs, reward=reward, done=True)
        
        obs = LegacyObservation(success=False, error_message="Invalid action")
        return StepResult(observation=obs, reward=0.01, done=False)

    def _grade_task(self, answer: str) -> float:
        cursor = self.conn.cursor()
        try:
            if self.task_level == "easy":
                # Changed 1.0 to 0.99 and 0.0 to 0.01
                return 0.99 if answer and ("3450.75" in answer) else 0.01
            elif self.task_level == "medium":
                cursor.execute("SELECT COUNT(*) FROM inventory;"); rows = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(stock_count) FROM inventory;"); stock = cursor.fetchone()[0]
                return 0.99 if (rows == 2 and stock == 50) else (0.5 if rows == 2 else 0.01)
            elif self.task_level == "hard":
                cursor.execute("PRAGMA table_info(transactions);"); cols = cursor.fetchall()
                type_ok = any('TEXT' in c[2].upper() for c in cols if c[1] == 'transaction_id')
                cursor.execute("SELECT COUNT(*) FROM transactions;"); count_ok = cursor.fetchone()[0] == 2
                return 0.99 if (type_ok and count_ok) else (0.5 if type_ok else 0.01)
        except: return 0.01
        return 0.01

# --- FASTAPI SERVER ---
app = FastAPI()
env = LegacyDataEnvironment()

@app.get("/")
def home(): return {"status": "running"}

@app.post("/reset")
async def reset(request: Request):
    try:
        body = await request.body()
        data = await request.json() if body else {}
    except:
        data = {}
    result = env.reset(task_level=data.get("task_level", "easy"))
    # Safely convert to dict for Phase 1 API
    return result.dict() if hasattr(result, "dict") else result

@app.post("/step")
async def step(request: Request):
    try:
        body = await request.body()
        data = await request.json() if body else {}
    except:
        data = {}
    result = env.step(data)
    # Safely convert to dict for Phase 1 API
    return result.dict() if hasattr(result, "dict") else result
