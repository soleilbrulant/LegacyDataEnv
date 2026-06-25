
# LegacyDataEnv - The Enterprise Database Agent Sandbox 🗄️

<div align="center">
  
  **AI Agent Testing Ground • Dense Reward Grading • Pluggable Schemas**
  
  ![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
  ![Hugging Face](https://img.shields.io/badge/Hosted_on-Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)

</div>

---

## 📌 Overview

**LegacyDataEnv** is an advanced, real-world Reinforcement Learning (RL) environment built on the `openenv-core` framework. It simulates a chaotic, 10-year-old legacy relational database, serving as a "flight simulator" to train Large Language Models (LLMs) to safely act as Backend Reliability Engineers.

Unlike generic text-to-SQL toys, this environment forces AI agents to handle dirty data, mixed data types, and strict foreign key constraints in a sandboxed, zero-risk environment before touching production systems.

## ✨ Key Features

### 🧠 **Intelligent Agent Evaluation**
- **Dense Partial Rewards**: Evaluates agents not just on completion, but on safety and precision (0.0 to 1.0 scoring).
- **Error Feedback Loops**: Raw SQLite engine errors are fed directly back into the agent's observation stream for self-correction.
- **Strict Constraint Enforcement**: Simulates real-world database architectures, including `PRAGMA foreign_keys = ON`.

### 🔄 **Pluggable Architecture**
- **Bring Your Own DB**: Seamlessly swap the default in-memory tables with massive, real-world databases (like the *Chinook Database* or corporate SQL dumps).
- **Multi-Mode Support**: Run as a standard Python module, a local HTTP API, or a Dockerized microservice.

### 📊 **Real-Time Developer Dashboard**
- **Interactive Web UI**: Watch your AI agents operate in real-time.
- **Visual Action Streams**: Monitor step-by-step SQL queries, observations, and reward fluctuations natively in the browser.

---

## 🎯 The Agent Tasks

Agents are placed into an environment with a specific difficulty tier, requiring increasingly advanced database engineering skills:

1. **🟢 Easy (Reconnaissance):** Extract mathematical maximum values from string columns contaminated with mixed currency symbols ($, €, £).
2. **🟡 Medium (Data Rescue):** Perform case-insensitive deduplication, merging canonical records while retaining maximum stock values.
3. **🔴 Hard (Schema Migration):** Migrate a legacy integer Primary Key to a TEXT UUID without violating strict relational Foreign Key constraints in connected tables.

---

## ⚙️ Action & Observation Space

### Actions
* `execute_sql`: Submits raw SQL to the engine. Returns the resulting rows or schema changes.
* `submit_solution`: Signals task completion to trigger the dense-reward grading algorithm.

### Observations
* `success`: Boolean indicating if the SQL executed without crashing the engine.
* `data`: JSON array of the resulting rows (if a SELECT query was run).
* `error_message`: Stack traces and SQLite errors for agent self-correction.
* `feedback`: Environment status and final task scores.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `uv` or `pip` package manager

### Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/soleilbrulant/LegacyDataEnv.git
cd LegacyDataEnv

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the Interactive Web Dashboard
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

Then, open `http://localhost:7860` in your browser to interact with the environment.

### Using a Real Database (e.g., Chinook)
To train your agents on massive real-world datasets rather than the default synthetic tables:
1. Download a `.sqlite` or `.db` file into the root directory.
2. Edit `envs/legacy_data/env.py`.
3. Change `self.db_path = ":memory:"` to `self.db_path = "your_database.sqlite"`.

---

## 🐳 Docker Deployment

To run the environment as an isolated, containerized server:
```bash
docker build -t legacy-data-env .
docker run -p 7860:7860 legacy-data-env
```

---

<div align="center">
  
**Powered by OpenEnv Core**

*Safe AI Training • Robust Evaluation • Open Source*

</div>
