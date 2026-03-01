import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

log_file = "test_minimax_output.txt"
with open(log_file, "w") as f:
    def log(msg):
        print(msg)
        f.write(msg + "\n")
        f.flush()

    key = os.environ.get("MINIMAX_API_KEY")
    log(f"Key preview: {key[:10]}...{key[-5:] if key else ''}")

    # Use the endpoint that didn't give 401
    base_url = "https://api.minimaxi.chat/v1"
    
    models = [
        "abab6.5s-chat",
        "abab6.5-chat",
        "abab6-chat",
        "abab5.5s-chat",
        "abab5.5-chat",
        "minimax-text-01",
        "gpt-3.5-turbo",
        "gpt-4",
    ]

    log(f"\n--- Testing base_url: {base_url} with multiple models ---")
    for model in models:
        log(f"Testing model: {model}")
        client = OpenAI(api_key=key, base_url=base_url)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            log(f"✅ Success with model {model}!")
            log(f"Response: {response.choices[0].message.content}")
            break # Stop if we find one
        except Exception as e:
            log(f"❌ Model {model} failed: {e}")
