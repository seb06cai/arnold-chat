# Arnold Coach — RAG-Enabled Voice Agent

> "Velcome to ze iron temple." — Arnold, 1977

**Live demo:** https://frontend-six-taupe-55.vercel.app/

---

## How it works

Click **BEGIN SESSION** and you're talking to Arnold Schwarzenegger, circa Gold's Gym Venice Beach 1977.

Under the hood: the frontend hits `/api/token` to get a LiveKit JWT, connects to LiveKit Cloud, and LiveKit dispatches the session to a Python agent running on EC2. From there it's a full voice pipeline — Deepgram transcribes what you say, GPT-4.1-mini figures out what Arnold should say back, and ElevenLabs speaks it. Silero handles turn detection so Arnold knows when you've finished talking.

On every substantive turn, the agent runs RAG over Arnold's *Encyclopedia of Modern Bodybuilding* and injects the most relevant passages into context before the LLM responds. The transcript shows Arnold's lines in gold on the left, yours in gray on the right.

---

## RAG

The source is Arnold's *Encyclopedia of Modern Bodybuilding* — the PDF is image-based, so it had to be OCR'd first (`pdf2image` + `pytesseract`). From there, the text gets split into ~512-token chunks, embedded with `text-embedding-3-small`, and stored in a FAISS index. The same chunks are kept as plain text for BM25.

At query time, retrieval is hybrid — FAISS top-4 for semantic matches, BM25 top-3 for keyword matches, deduplicated down to ≤5 passages. Short responses like "yes" or "ok" skip retrieval entirely to avoid unnecessary latency. When the `get_exercise_form_cues` tool is called, the query is sharpened to `"{exercise} technique execution form"` for more targeted results.

Retrieved passages get injected as context before the LLM generates its response. The pre-built index lives in `agent/storage/` and is committed to the repo — the agent loads it at startup and never rebuilds it.

---

## Tools

| Tool | Triggered by | What it does |
|------|-------------|--------------|
| `get_exercise_form_cues` | Any exercise form or technique question | Runs RAG with a targeted query and returns cues from the Encyclopedia |
| `generate_workout_plan` | Training plan requests | Returns a weekly plan based on goal, experience, and schedule |
| `get_arnold_quote` | Motivation, doubt, or encouragement | Returns an Arnold quote matched to the tone |

---

## Stack

| | |
|---|---|
| Voice agent | LiveKit Agents v1.x (Python) |
| STT | Deepgram Nova-3 |
| LLM | OpenAI GPT-4.1-mini |
| TTS | ElevenLabs `eleven_turbo_v2_5` |
| VAD | Silero |
| RAG | LlamaIndex 0.10.x + FAISS + `bm25s` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Frontend | Next.js 15, LiveKit Components React |
| Hosting | Vercel (frontend), AWS EC2 (agent) |

---

## Design decisions

**Hybrid retrieval (FAISS + BM25)**
Vector search alone wasn't enough. "Preacher curl" and "concentration curl" are semantically close, so a pure embedding search would blur them together. Adding BM25 keeps exact exercise names from getting lost. The combo handles both fuzzy intent ("how do I build my chest") and specific terminology reliably.

**Fixed-size chunking**
The Encyclopedia is already organized by exercise — one section per movement. Simple fixed-size chunks worked fine for this structure without needing anything fancier.

**A race condition I had to squash**
LiveKit can start generating a response before RAG finishes injecting context. When it did, the model would see the new context, regenerate — and skip tool calls the second time around every time. Turning off preemptive generation fixed it. Slight latency tradeoff but the correctness was worth it.

**Sessions and cleanup**
Each session gets a unique room name so concurrent users are fully isolated. When someone closes the tab, LiveKit notifies the agent and it exits cleanly — no zombie sessions sitting around.

**What I'd do differently**
Word-level streaming on the transcript so responses appear as they're spoken rather than all at once. The current per-utterance approach works but feels a bit choppy.
