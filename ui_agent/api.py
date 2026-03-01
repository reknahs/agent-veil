import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from .classifier import classify_site
from .bug_generator import generate_bugs
from .bug_tester import run_all_tests
from .bug_filter import filter_real_bugs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Agent API Started")
    yield
    # Shutdown logic
    print("Agent API Shutting down")

app = FastAPI(lifespan=lifespan, title="UI/UX Bug Finder API")

class AnalyzeRequest(BaseModel):
    url: str
    max_steps: int = 55 # Configurable steps

async def stream_analysis(url: str, max_steps: int):
    minimax_key = os.getenv("MINIMAX_API_KEY", "")
    if not minimax_key:
        yield json.dumps({"status": "error", "message": "MINIMAX_API_KEY not configured in env."}) + "\n"
        return

    try:
        # Step 1: Classify
        yield json.dumps({"status": "info", "message": f"Step 1: Classifying website at {url}..."}) + "\n"
        classification = await classify_site(url)
        yield json.dumps({"status": "info", "message": f"Classified as: {classification.get('classification', 'unknown')}"}) + "\n"

        # Step 2: Generate
        yield json.dumps({"status": "info", "message": "Step 2: Generating 12 potential UI/UX bugs via LLM..."}) + "\n"
        bugs = generate_bugs(classification, url, minimax_key)
        yield json.dumps({"status": "info", "message": f"Generated {len(bugs)} potential bugs to test."}) + "\n"

        yield json.dumps({"status": "info", "message": "Step 3: Launching browser-use. Bugs will be streamed here in real-time as they are found..."}) + "\n"

        # We will use an asyncio Queue to pass messages from the browser-use callback to the HTTP stream
        stream_queue = asyncio.Queue()
        
        # Keep track of how many bugs we yield
        yielded_count = 0

        async def handle_new_bug(result):
            """Callback fired by browser-use the moment it finishes testing a specific bug."""
            nonlocal yielded_count
            
            if result.status == "fail":
                # Immediately pass this single bug to the LLM strict filter!
                # filter_real_bugs expects a list of dicts.
                kept_ids = filter_real_bugs([result.__dict__], minimax_key)
                
                if result.bug_id in kept_ids:
                    # It's a real bug, send it to the queue!
                    yielded_count += 1
                    bug_str = f"Bug #{yielded_count}: [{result.category}] {result.bug_name}\nDetail: {result.detailed_report}\n\n"
                    # We push to the queue so the main thread can yield it
                    await stream_queue.put({"status": "bug", "content": bug_str})
                else:
                    await stream_queue.put({"status": "info", "message": f"Agent found an issue ('{result.bug_name}'), but strict LLM filter flagged it as a subjective suggestion and removed it."})
            elif result.status == "pass":
                await stream_queue.put({"status": "info", "message": f"Agent explicitly passed: {result.bug_name}"})

        # Background task: Run the browser agent
        async def run_agent():
            try:
                await run_all_tests(
                    bugs=bugs, 
                    site_url=url, 
                    max_steps=max_steps,
                    on_bug_reported=handle_new_bug
                )
            except Exception as e:
                await stream_queue.put({"status": "error", "message": f"Browser agent crashed: {str(e)}"})
            finally:
                # Send a sentinel value to close the queue
                await stream_queue.put(None)

        # Kick off the agent in the background
        agent_task = asyncio.create_task(run_agent())

        # Yield from the queue as items arrive!
        while True:
            item = await stream_queue.get()
            if item is None:
                # Sentinel received, agent is done
                break
            
            yield json.dumps(item) + "\n"

        await agent_task # ensure cleanup
        
        yield json.dumps({"status": "info", "message": f"Testing complete. Total strict UI/UX bugs found: {yielded_count}"}) + "\n"
        yield json.dumps({"status": "done", "message": "All issues have been streamed."}) + "\n"

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield json.dumps({"status": "error", "message": str(e)}) + "\n"

@app.post("/analyze")
async def analyze_website(request: AnalyzeRequest):
    """
    Kicks off the full UI/UX testing workflow.
    Returns a stream of JSON messages over HTTP lines (JSON-Line format).
    """
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http/https.")
        
    return StreamingResponse(
        stream_analysis(request.url, request.max_steps),
        media_type="application/x-ndjson"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui_agent.api:app", host="0.0.0.0", port=8000, reload=False)
