# AgentVeil 🕵️‍♂️✨

**Automated AI Security & UX Auditing Pipeline**

AgentVeil is a next-generation, autonomous security and user experience (UX) auditing platform. It bridges the gap between static code analysis and dynamic testing by deploying multiple specialized AI agents to crawl, analyze, and automatically fix vulnerabilities in web applications in real-time.

---

## 🏗️ Core Architecture & Tech Stack

AgentVeil is built on a modern, highly concurrent, and cloud-native stack designed for speed and reliability.

### The Frontend Dashboard
*   **Next.js (React 18)**: The core framework for the dashboard, providing seamless Server-Side Rendering (SSR) and API routes.
*   **Tailwind CSS**: Used for rapid, responsive, and beautiful styling of the dashboard interface.
*   **TypeScript**: Ensures type safety across the frontend and API proxy routes.

### The Backend Databases & APIs
*   **Convex**: The primary database and real-time synchronization engine. Convex allows the dashboard to instantly reflect new vulnerabilities found by the agents without manual polling. It seamlessly bridges the AI backend with the React frontend.
*   **FastAPI / Uvicorn (Python)**: The backbone of the agent APIs. Both the Logic Agent, UI Agent, and Fixer services run as robust Python FastAPI microservices, providing endpoints for triggering scans and generating pull requests.

### AI Models & Tooling
*   **MiniMax API (`minimax-text-01`)**: The core Large Language Model used by the *Fixer Agent*. MiniMax provides lightning-fast inference capabilities, allowing AgentVeil to analyze broken code snippets and output complete, corrected files instantly.
*   **Browser Use**: The driving force behind the *UI Agent*. Browser Use allows an AI agent to spin up a headless Chromium instance, physically navigate through the target website like a human user, and visually inspect rendering issues, broken links, or UX flaws.
*   **Gemini 2.0 Flash / OpenAI (Python)**: Used for rapid classification, reasoning, and generating prompts during the logic scanning phases.

---

## 🤖 The Three-Agent System

AgentVeil utilizes a multi-agent orchestrated approach, dividing the massive task of application auditing into three distinct, specialized workers:

### 1. The Logic Agent 🧠 (Vulnerability & Security Scanner)
The Logic Agent focuses on the invisible threats:
*   **Static Code Analysis**: It reviews the GitHub repository structure to understand the application routing and architecture.
*   **Dynamic Endpoint Testing**: It actively probes the target URL for common vulnerabilities like SQL Injection, Broken Access Control, and SSRF (Server-Side Request Forgery).
*   **Real-time Streaming**: Discovered breaches are streamed in raw time via Server-Sent Events (SSE) directly to the Next.js dashboard, providing instant feedback.

### 2. The UI / UX Agent 🎨 (Visual Inspector)
The UI Agent focuses on what the user actually sees:
*   **Headless Navigation (`browser-use`)**: It spins up a browser and actively clicks through the application, looking for layout shifts, missing images, unhandled 404s, or poor accessibility (a11y) practices.
*   **Console Monitoring**: It monitors the browser console for silent JavaScript errors and network failures that might degrade the user experience.
*   **Concurrent Execution**: The UI Agent runs in parallel with the Logic Agent, allowing a full-stack audit to occur in half the time.

### 3. The Fixer Agent 🛠️ (Automated Remediation)
AgentVeil doesn't just find problems; it fixes them.
*   **Contextual Patching**: When an error is found, the Fixer reads the exact GitHub file related to that route.
*   **MiniMax LLM Generation**: It sends the error logs and the full file content to the `minimax-text-01` model, requesting a fully repaired, correct file.
*   **Automated Pull Requests (PRs)**: The Fixer uses the GitHub API to automatically create a new branch containing the fix, and opens a Pull Request directly against the user's repository, complete with a detailed summary.

---

## 💡 Key Concepts & Techniques

*   **Repository Normalization**: The system automatically intelligently parses full GitHub URLs down to their `owner/repo` formats, ensuring the GitHub API can always find the correct files regardless of how the user inputs them.
*   **Dynamic Branch Slugification**: When creating PRs, the system automatically translates AI-generated error titles into valid, URL-safe branch names (e.g., stripping brackets and ampersands) to prevent GitHub `422` reference errors.
*   **Rate Limits and Concurrency**: The dashboard safely handles large numbers of concurrent Agent runs without crashing, gracefully queuing Fixer fixes to ensure API rate limits (like MiniMax constraints) are respected.
*   **Virtual Environment Isolation**: The Python agents use isolated `.venv` environments to prevent dependency conflicts between FastApi, Browser Use, and standard libraries.

---

## 🚀 Running the Project Locally

AgentVeil is designed to run entirely locally via a single orchestration script. It will automatically handle virtual environments, background processes, and port management.

**1. Set up your Environment Variables**
Copy the example environment file and insert your dedicated API keys.
```bash
cp .env.example .env
```
Ensure `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, and `BROWSER_USE_API_KEY` are explicitly populated.

**2. Start the AgentVeil Cluster**
Launch the interactive Bash script to spin up the React frontend and all 3 Python microservice APIs concurrently.
```bash
sh start_local.sh
```

**3. Analyze!**
The script will automatically open your default browser to `http://localhost:3000`. Enter your target Website URL and its associated GitHub Repository, then click **Analyze** to watch the agents get to work!

*(To stop the entire cluster instantly, press `Ctrl+C` once in your terminal.)*
