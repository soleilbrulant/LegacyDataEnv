import os
import json
from openai import OpenAI
from envs.legacy_data.env import LegacyDataEnvironment
from envs.legacy_data.models import LegacyAction

# 1. SETUP LLM CLIENT
# We use the Hugging Face Serverless API which acts exactly like OpenAI's API.
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("⚠️ WARNING: HF_TOKEN environment variable not set.")
    print("Please set it to run this script: export HF_TOKEN='your_hf_token'")
    exit(1)

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# 2. INITIALIZE ENVIRONMENT
env = LegacyDataEnvironment()

def get_llm_action(system_prompt: str, history: list) -> LegacyAction:
    """Calls the LLM to get the next action (execute_sql or submit_solution)."""
    
    # We ask the LLM to output pure JSON
    messages = [{"role": "system", "content": system_prompt}] + history
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    result_text = response.choices[0].message.content
    try:
        data = json.loads(result_text)
        return LegacyAction(**data)
    except Exception as e:
        print(f"Failed to parse LLM response: {result_text}")
        raise e

def run_agent(task_level: str):
    print(f"\n🚀 Starting Agent on Task Level: {task_level.upper()}\n")
    obs = env.reset(task_level=task_level)
    
    # Define the "Persona" and rules for the AI
    system_prompt = f"""You are an AI Database Reliability Engineer.
Your task level is '{task_level}'. 
For Easy: Extract max values from columns contaminated with mixed currency symbols.
For Medium: Perform case-insensitive deduplication retaining rows with the maximum specific values.
For Hard: Migrate an integer primary key to a text UUID without violating strict relational Foreign Key constraints.

You interact with an SQLite database.
You must reply with a raw JSON object matching one of these two structures:

To execute a query:
{{
  "action_type": "execute_sql",
  "sql_query": "SELECT * FROM table;"
}}

To submit the final answer once you verified your solution:
{{
  "action_type": "submit_solution",
  "answer": "Your detailed explanation of what you did or the final answer."
}}

Always check the database schema first if you don't know it!
"""

    history = [
        {"role": "user", "content": f"The environment is ready. Initial observation: {obs.model_dump_json()}"}
    ]

    step_count = 0
    max_steps = 10
    
    while step_count < max_steps:
        step_count += 1
        print(f"\n--- Step {step_count} ---")
        
        # 1. Get Action from LLM
        print("🤔 Agent is thinking...")
        action = get_llm_action(system_prompt, history)
        
        if action.action_type == "execute_sql":
            print(f"🛠️  Agent executes SQL:\n{action.sql_query}")
        else:
            print(f"🎯 Agent submits solution:\n{action.answer}")
            
        history.append({"role": "assistant", "content": action.model_dump_json()})
        
        # 2. Step the Environment
        obs = env.step(action)
        
        # 3. Observe the results
        obs_json = obs.model_dump_json()
        print(f"🌍 Environment replies:\n{obs_json}")
        
        history.append({"role": "user", "content": f"Environment Observation: {obs_json}"})
        
        if obs.done:
            print(f"\n✅ Task Finished! Final Reward: {obs.reward}")
            break
            
    if step_count >= max_steps:
        print("\n❌ Reached maximum steps without finishing.")

if __name__ == "__main__":
    # Let's run the easy task
    run_agent("easy")
