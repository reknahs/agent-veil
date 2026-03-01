# GAN-like Agent Testing Framework

Multi-agent framework that uses a **Generator** (Minimax) and **Discriminator** (Browser Use) to find errors on a website. The generator produces diverse user workflows; the discriminator runs them in a real browser and reports failures.

- **Generator**: Minimax LLM generates many different test workflows (e.g. "Open Tops and add the second item to cart").
- **Discriminator**: Browser Use agent executes each workflow and extracts errors (failed steps, non-finished status, judge verdict).

Feedback from the discriminator can be fed back into the generator in the next round to produce more edge-case workflows (GAN-like loop).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` from the example and set your keys:

```bash
cp .env.example .env
# Edit .env: BROWSER_USE_API_KEY, MINIMAX_API_KEY, MINIMAX_GROUP_ID
```

## Usage

```bash
# Default: 2 rounds, 5 workflows, generic e-commerce description
python main.py

# Any site: set URL and (optionally) what the site has
python main.py --url https://example.com/shop --site-description "Categories: A, B, C. No search. Add to cart only."

# Or put the description in a file
python main.py --url https://mysite.com --description-file ./mysite-desc.txt

# Custom rounds and workflows
python main.py --rounds 3 --workflows-per-round 8

# JSON report
python main.py -o report.json
```

## Using Multiple / Any Website

The framework is **site-agnostic**. For each run:

- **`--url`** / `TARGET_URL`: The site to test (any URL).
- **`--site-description`** / **`-d`** / **`SITE_DESCRIPTION`**: What the site has (nav, categories, etc.). Generator only suggests workflows using these. If omitted, generic e-commerce description is used.
- **`--description-file`**: Path to a text file with the site description. **`AGENT_INSTRUCTIONS`** (env): Optional extra instructions for the browser agent.

## Architecture

```
┌─────────────────┐     workflows      ┌──────────────────┐
│   Generator     │ ────────────────►  │   Discriminator   │
│   (Minimax)     │                    │   (Browser Use)  │
└────────▲────────┘                    └────────┬─────────┘
         │                                       │
         │         feedback (errors)             │
         └───────────────────────────────────────┘
```

- **Round N**: Generator produces K workflows → Discriminator runs each → errors collected.
- **Round N+1**: Generator receives a summary of errors and produces a new set of workflows (including edge cases).

## API Keys (testing only)

Store in `.env`; do not commit:

- **Browser Use**: [Browser Use Cloud](https://docs.cloud.browser-use.com/) — `BROWSER_USE_API_KEY`
- **Minimax**: [MiniMax Platform](https://platform.minimax.io/) — `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`
