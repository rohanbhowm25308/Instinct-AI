# Instinct AI

Rebranded from SENTINEL X AI. Login features a animated falling cyan light particles and keeps the original 3D flip transition. The decorative code panel has been removed.

## Run

1. Create a virtual environment and install `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set `GROQ_API_KEY` and a random `SECRET_KEY`.
3. Run `python app.py` and visit `http://127.0.0.1:5000`.

Groq model default: `openai/gpt-oss-120b`. Search-backed fact verification additionally requires a search API key.

Never commit `.env` or expose your API key.

## Dense falling lights update
The login/signup background now renders approximately four times as many light streaks at typical desktop resolutions, with brighter dots, longer trails, and faster motion. The glass login flip and all backend routes are unchanged.


Login background: larger, brighter cyan/violet falling lights with glowing heads and longer trails. No API keys are bundled.


## Dedicated modules (06–15)
Modules 06–15 have their own interactive labs (static code review, event timeline, trust metrics, evidence rewrite, adversarial evaluation, downloadable audit, response comparison, event inspector, speech transcription and mission dashboard). Their outputs are grounded in input, Groq responses or your saved audit history; missing external evidence remains unverified.

Copy `.env.example` to `.env`, configure your own API credentials and a strong SECRET_KEY, then run `pip install -r requirements.txt` and `python app.py`. Existing `sentinel.db` should be kept locally if you need previous accounts and audit history; never publish it. This ZIP deliberately excludes it.

## INSTINCT X — separate experiences section

The existing workspace/modules are preserved. Scroll below the feature cards to the **INSTINCT X** section (or select INSTINCT X in the top navigation).

New experiences: Digital Twin, Debate Colosseum, Futureverse, Neural Memory Galaxy, Reality Lens, Agent Mission Control, AI Escape Room, Invention Studio, Voice Command Nexus, Strategy Arena.

**Setup:** Install `requirements.txt`, set `SECRET_KEY` and `GROQ_API_KEY` in `.env` or Render environment settings, then start the Flask app. Optional `GROQ_VISION_MODEL` controls the vision-capable model for Reality Lens (default `meta-llama/llama-4-scout-17b-16e-instruct`; verify that this model is available on your Groq account). AI requests are subject to provider availability and a 24-second network timeout. Browser speech recognition requires a supported browser and microphone permission. Speech synthesis requires browser support. The Mission Control feature generates plans only and **does not execute external actions**. Reality Lens visual observations do not authenticate images. Escape Room includes three local playable puzzles; more can be added in `static/instinct-x.js`. Knowledge nodes persist per signed-in user in the existing SQLite database, with a 100-item limit. SQLite storage on an ephemeral Render filesystem will not persist reliably across deployments; use a persistent disk or external database for production.

**Verification:** Python files compile and JS passes `node --check`. Full Flask integration tests were not executed in this build environment because Flask was not installed; test authentication, AI API configuration, uploads, and browser microphone access before publishing.


## Instant Flow — Project Build Journey

The previous Website Guardian section was replaced with **Instant Flow**, a project case-study builder. Sign in, navigate to Instant Flow, enter project information, optionally add contribution estimates, manage milestones, upload screenshots/videos, save, preview, publish, and share your project page at `/flow/<unique-slug>`. Unpublished pages and media are accessible only to their owner. Contribution estimates are self-reported and not independently verified.

Data is stored in `sentinel.db` and media in `flow_media/`. **Render free/ephemeral instances do not persist local files between deployments/restarts**; for production, configure a persistent disk (where supported) or migrate to a managed PostgreSQL database and object storage. The current implementation is suitable for local development and small single-instance demos, not durable production hosting. Upload limit: 25 MB per file; allowed PNG/JPG/WEBP/GIF/MP4/WEBM. Public pages become visible to anyone with the link after publishing.

The project's `.env` and local database are intentionally omitted from the distributable ZIP to protect credentials and private user data. Copy `.env.example` to `.env` and configure `SECRET_KEY` and `GROQ_API_KEY` as needed.
