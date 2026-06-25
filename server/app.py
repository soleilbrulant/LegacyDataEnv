"""
FastAPI application for the LegacyDataEnv Environment.

Bug Fix #7: Replace hand-rolled FastAPI with the official create_app() factory.
This sets up the correct /reset, /step, /state, /schema, /health, and /ws
endpoints that the OpenEnv validator expects, with proper serialization.

Endpoints (managed by create_app):
    - POST /reset  : Reset the environment
    - POST /step   : Execute an action
    - GET  /state  : Get current environment state
    - GET  /schema : Get action/observation/state JSON schemas
    - GET  /health : Health check
    - WS   /ws     : WebSocket endpoint for persistent sessions

Usage:
    uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
"""

from openenv.core.env_server import create_app

try:
    from ..models import LegacyAction, LegacyObservation
    from ..env import LegacyDataEnvironment
except ImportError:
    from envs.legacy_data.models import LegacyAction, LegacyObservation
    from envs.legacy_data.env import LegacyDataEnvironment


# Create the fully-compliant OpenEnv FastAPI application
app = create_app(
    LegacyDataEnvironment,
    LegacyAction,
    LegacyObservation,
    env_name="legacy-data-env",
    max_concurrent_envs=4,
)

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LegacyDataEnv Simulator</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; }
            .font-mono { font-family: 'Fira Code', monospace; }
            .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body class="bg-gray-900 text-gray-100 min-h-screen flex flex-col items-center py-10 px-4">
        
        <div class="max-w-4xl w-full">
            <header class="mb-8 text-center">
                <h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">LegacyDataEnv</h1>
                <p class="text-gray-400 mt-2">RL Environment Playground</p>
            </header>

            <!-- Controls -->
            <div class="glass p-6 rounded-xl border border-gray-700 shadow-2xl mb-6">
                <div class="flex flex-wrap gap-4 items-center justify-between">
                    <div class="flex items-center gap-3">
                        <label class="font-semibold text-sm uppercase tracking-wide text-gray-400">Task Level:</label>
                        <select id="task_level" class="bg-gray-800 border border-gray-600 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 outline-none transition">
                            <option value="easy">Easy (Extract Max)</option>
                            <option value="medium">Medium (Deduplicate)</option>
                            <option value="hard">Hard (Schema Migration)</option>
                        </select>
                        <button onclick="resetEnv()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded font-medium transition shadow-lg shadow-indigo-600/20">Reset DB</button>
                    </div>
                    <div class="text-sm font-mono text-gray-400">
                        Status: <span id="status-indicator" class="text-yellow-400">Waiting...</span>
                    </div>
                </div>
            </div>

            <!-- Terminal Output -->
            <div class="bg-black rounded-xl border border-gray-800 shadow-2xl overflow-hidden mb-6 flex flex-col h-[400px]">
                <div class="bg-gray-800 px-4 py-2 flex items-center gap-2 border-b border-gray-700">
                    <div class="w-3 h-3 rounded-full bg-red-500"></div>
                    <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                    <span class="text-xs font-mono text-gray-400 ml-2">observation_stream</span>
                </div>
                <div id="terminal" class="p-4 font-mono text-sm overflow-y-auto flex-1 text-gray-300 whitespace-pre-wrap"></div>
            </div>

            <!-- Agent Input Form -->
            <div class="glass p-6 rounded-xl border border-gray-700 shadow-2xl">
                <h3 class="text-lg font-semibold mb-4 text-indigo-300">Agent Action</h3>
                
                <div class="flex flex-col gap-4">
                    <div class="flex items-center gap-4">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="action_type" value="execute_sql" checked class="text-indigo-500 focus:ring-indigo-500">
                            <span>execute_sql</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="action_type" value="submit_solution" class="text-indigo-500 focus:ring-indigo-500">
                            <span>submit_solution</span>
                        </label>
                    </div>

                    <div id="sql_input_group">
                        <textarea id="sql_query" rows="3" placeholder="SELECT * FROM usr_accnts;" class="w-full bg-gray-800 border border-gray-600 rounded p-3 font-mono text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition"></textarea>
                    </div>

                    <div id="submit_input_group" class="hidden">
                        <input type="text" id="answer" placeholder="Final answer or explanation..." class="w-full bg-gray-800 border border-gray-600 rounded p-3 font-mono text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition">
                    </div>

                    <div class="flex justify-end">
                        <button onclick="sendStep()" class="bg-purple-600 hover:bg-purple-500 text-white px-6 py-2 rounded font-medium transition shadow-lg shadow-purple-600/20">Send Action</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const terminal = document.getElementById('terminal');
            const statusInd = document.getElementById('status-indicator');
            const radios = document.getElementsByName('action_type');
            
            // Toggle input fields based on action type
            radios.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    if (e.target.value === 'execute_sql') {
                        document.getElementById('sql_input_group').classList.remove('hidden');
                        document.getElementById('submit_input_group').classList.add('hidden');
                    } else {
                        document.getElementById('sql_input_group').classList.add('hidden');
                        document.getElementById('submit_input_group').classList.remove('hidden');
                    }
                });
            });

            function log(msg, type='info') {
                const el = document.createElement('div');
                el.className = 'mb-2';
                if (type === 'user') el.innerHTML = `<span class="text-indigo-400">Agent></span> ${msg}`;
                else if (type === 'env') el.innerHTML = `<span class="text-green-400">Env></span> <span class="text-gray-300">${msg}</span>`;
                else if (type === 'error') el.innerHTML = `<span class="text-red-400">Error></span> ${msg}`;
                else el.innerHTML = msg;
                
                terminal.appendChild(el);
                terminal.scrollTop = terminal.scrollHeight;
            }

            async function resetEnv() {
                const level = document.getElementById('task_level').value;
                log(`Calling /reset with task_level="${level}"...`, 'user');
                statusInd.textContent = "Resetting...";
                statusInd.className = "text-yellow-400";
                
                try {
                    const res = await fetch('/reset', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task_level: level})
                    });
                    const data = await res.json();
                    log(JSON.stringify(data, null, 2), 'env');
                    statusInd.textContent = "Ready";
                    statusInd.className = "text-green-400";
                } catch (e) {
                    log(e.toString(), 'error');
                    statusInd.textContent = "Error";
                    statusInd.className = "text-red-400";
                }
            }

            async function sendStep() {
                const actionType = document.querySelector('input[name="action_type"]:checked').value;
                let payload = { action_type: actionType };
                
                if (actionType === 'execute_sql') {
                    payload.sql_query = document.getElementById('sql_query').value;
                } else {
                    payload.answer = document.getElementById('answer').value;
                }

                log(`Sending action: ${JSON.stringify(payload)}`, 'user');
                statusInd.textContent = "Processing...";
                statusInd.className = "text-yellow-400";
                
                try {
                    const res = await fetch('/step', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({action: payload})
                    });
                    const data = await res.json();
                    log(JSON.stringify(data, null, 2), 'env');
                    
                    if (data.done) {
                        statusInd.textContent = `Done (Reward: ${data.reward})`;
                        statusInd.className = "text-purple-400";
                    } else {
                        statusInd.textContent = "Ready";
                        statusInd.className = "text-green-400";
                    }
                } catch (e) {
                    log(e.toString(), 'error');
                    statusInd.textContent = "Error";
                    statusInd.className = "text-red-400";
                }
            }

            // Init on load
            resetEnv();
        </script>
    </body>
    </html>
    """


def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for the openenv-server CLI script defined in pyproject.toml."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LegacyDataEnv Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    main(host=args.host, port=args.port)