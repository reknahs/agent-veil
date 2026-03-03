import os
from daytona import Daytona, DaytonaConfig, CreateSandboxBaseParams, SessionExecuteRequest

daytona = Daytona(DaytonaConfig(api_key="dtn_44a46166cb25ea8736f9a1e0f0488bb92951280eee1c533a5148b1a6e73558be"))

# Create a long-lived sandbox
print("Creating/Accessing Sandbox...")
sandbox = daytona.create(CreateSandboxBaseParams(
    language="python",
    auto_stop_interval=0,
))

# Clone your repo into the sandbox
print("Cloning repository...")
sandbox.process.exec("rm -rf /home/daytona/agentveil") # Clean start
sandbox.git.clone("https://github.com/reknahs/agent-veil.git", "/home/daytona/agentveil")

# Install cloudflared for public tunnels locally in the repo dir
print("Installing Cloudflare...")
sandbox.process.exec("curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /home/daytona/agentveil/cloudflared && chmod +x /home/daytona/agentveil/cloudflared")

# Set environment variables
sandbox.process.exec("""cat > /home/daytona/agentveil/.env << 'EOF'
MINIMAX_API_KEY=[YOUR_MINIMAX_API_KEY_HERE]
MINIMAX_GROUP_ID=[YOUR_MINIMAX_GROUP_ID_HERE]
BROWSER_USE_API_KEY=[YOUR_BROWSER_USE_API_KEY_HERE]
GITHUB_TOKEN=[YOUR_GITHUB_TOKEN_HERE]
EOF""")

# Start all three agents and tunnels in the background
session_id = "agentveil-session"
try:
    sandbox.process.create_session(session_id)
except:
    pass # Session might already exist

# Install ALL dependencies at once (in background to avoid SDK timeout)
print("Installing all dependencies (this will take a minute)...")
deps = "browser-use browser-use-sdk==3.1.0 playwright fastapi uvicorn pydantic python-dotenv openai"
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command=f"cd /home/daytona/agentveil && nohup bash -c 'pip install {deps} && playwright install --with-deps chromium' > install.log 2>&1 &",
    run_async=True
))

print("Waiting 60 seconds for dependencies to install...")
import time
time.sleep(60)

# Start Python Agents in background
print("Starting Python Agents...")
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python -m ui_agent.api > ui.log 2>&1 &",
    run_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python -m fixer.api > fixer.log 2>&1 &",
    run_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command="cd /home/daytona/agentveil && nohup python logic_agent/api.py > logic.log 2>&1 &",
    run_async=True
))

# Start Tunnels (SSH-based via localhost.run, extremely reliable)
print("Starting tunnels...")
ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt"
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command=f"cd /home/daytona/agentveil && nohup ssh -R 80:localhost:8000 {ssh_opts} nokey@localhost.run > ui_tunnel.log 2>&1 &",
    run_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command=f"cd /home/daytona/agentveil && nohup ssh -R 80:localhost:8001 {ssh_opts} nokey@localhost.run > fixer_tunnel.log 2>&1 &",
    run_async=True
))
sandbox.process.execute_session_command(session_id, SessionExecuteRequest(
    command=f"cd /home/daytona/agentveil && nohup ssh -R 80:localhost:8002 {ssh_opts} nokey@localhost.run > logic_tunnel.log 2>&1 &",
    run_async=True
))

print("Waiting for tunnels to establish (15s)...")
import time
urls = {}
ports = {"UI (8000)": "ui_tunnel.log", "Fixer (8001)": "fixer_tunnel.log", "Logic (8002)": "logic_tunnel.log"}

for i in range(15):
    time.sleep(1)
    for name, log in ports.items():
        if name in urls: continue
        try:
            res = sandbox.process.exec(f"cat /home/daytona/agentveil/{log}")
            if res.exit_code == 0:
                import re
                match = re.search(r'https://[a-zA-Z0-9-]+\.lhr\.life', res.result)
                if match:
                    urls[name] = match.group(0)
        except:
            pass
    if len(urls) == 3: break

if len(urls) < 3:
    print("\n⚠️  Warning: Some tunnels failed to start. Check logs in the sandbox at /home/daytona/agentveil/*.log")

print("\n--- DEPLOYMENT SUCCESSFUL ---")
for name, url in urls.items():
    print(f"{name} URL: {url}")

print(f"\nUpdate these in your Vercel Environment Variables!")
print(f"Sandbox ID: {sandbox.id}")