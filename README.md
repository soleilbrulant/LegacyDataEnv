# LegacyDataEnv 🗄️

An advanced, real-world OpenEnv environment simulating a chaotic, 10-year-old legacy SQLite database. Designed to test an AI agent's ability to act as a backend reliability engineer. 

Unlike standard "text-to-SQL" toys, this environment forces agents to handle dirty data, mixed types, and strict foreign key constraints, using a dense partial-reward grading algorithm.

## Tasks
1. **Easy (Reconnaissance):** Extract max values from columns contaminated with mixed currency symbols ($, €, £).
2. **Medium (Data Rescue):** Perform case-insensitive deduplication while retaining rows with the maximum specific values.
3. **Hard (Schema Migration):** Migrate an integer primary key to a text UUID without violating strict relational Foreign Key constraints.

## Action Space
* `execute_sql`: Accepts a string containing the raw SQL query to run against the in-memory database.
* `submit_solution`: Accepts a string containing the final answer or declaration of task completion.

## Observation Space
* `success`: Boolean indicating if the SQL executed without crashing.
* `data`: JSON array of the resulting rows (if a SELECT query was run).
* `error_message`: Raw SQLite engine errors fed back to the agent for self-correction.
* `feedback`: Environment status and final task scores (0.0 to 1.0).

## Local Setup
```bash
pip install -r requirements.txt
python test_inference.py