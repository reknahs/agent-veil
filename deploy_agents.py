import os
from daytona import Daytona, DaytonaConfig, CreateSandboxBaseParams, SessionExecuteRequest

daytona = Daytona(DaytonaConfig(api_key="dtn_44a46166cb25ea8736f9a1e0f0488bb92951280eee1c533a5148b1a6e73558be"))

# Create a long-lived sandbox (set auto_stop_interval=0 to keep it running)
sandbox = daytona.create(CreateSandboxBaseParams(
    language="python",
    auto_stop_interval=0,  # Disable auto-stop so agents run 24/7
))

# Clone your repo into the sandbox
sandbox.git.clone("https://github.com/reknahs/agent-veil.git", "/home/daytona/agentveil")

# Install dependencies
sandbox.process.exec("pip install -r /home/daytona/agentveil/logic_agent/requirements.txt")
sandbox.process.exec("pip install -r /home/daytona/agentveil/fixer/requirements.txt")
sandbox.process.exec("playwright install --with-deps chromium")

# Set environment variables
sandbox.process.exec("""cat > /home/daytona/agentveil/.env << 'EOF'
MINIMAX_API_KEY=your_key_here
MINIMAX_GROUP_ID=your_group_id
BROWSER_USE_API_KEY=your_browser_use_key
GITHUB_TOKEN=your_github_token
EOF""")

# Start all three agents in the background
session_id = "agentveil-session"
sandbox.process.create_session(session_id)

sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python logic_agent/api.py > logic.log 2>&1 &",
    var_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python -m ui_agent.api > ui.log 2>&1 &",
    var_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python -m fixer.api > fixer.log 2>&1 &",
    var_async=True
))

# Get the public preview URL for port 8001
preview = sandbox.get_preview_link(8001)
print(f"Fixer API is live at: {preview.url}")
print(f"Sandbox ID (save this!): {sandbox.id}")