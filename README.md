# Arnold Coach — RAG-Enabled Voice Agent

> "Velcome to ze iron temple." — Arnold, 1977

**Live demo:** https://frontend-six-taupe-55.vercel.app/

---

## How It Works (End-to-End)

1. The user opens the frontend and clicks **BEGIN SESSION**.
2. The Next.js frontend calls `POST /api/token`, which generates a signed LiveKit JWT and configures the room to dispatch the `arnold-coach` agent worker.
3. The browser connects to LiveKit Cloud via the LiveKit JS SDK.
4. LiveKit Cloud dispatches the room job to the Python agent worker running on AWS EC2.
5. The agent greets the user with Arnold's opening line, then listens and responds in real time using a full voice pipeline: Deepgram STT → GPT-4.1-mini LLM → ElevenLabs TTS, with Silero VAD for turn detection.
6. On each substantive user turn, the agent runs hybrid RAG retrieval over Arnold's *Encyclopedia of Modern Bodybuilding* and injects the most relevant passages as context before the LLM generates a response.
7. The frontend displays a live transcript, with Arnold's lines styled in gold on the left and the user's lines in gray on the right.

---

## RAG Integration

**Source:** Arnold Schwarzenegger's *Encyclopedia of Modern Bodybuilding* (~1,100 chunks after OCR and splitting).

**Indexing (`agent/ingest.py`):**
- OCR via `pdf2image` + `pytesseract` (the PDF is image-based, not text-based)
- Text split into ~512-token chunks with 50-token overlap via `llama-index`
- Embedded with `text-embedding-3-small` and stored in a FAISS index
- The same chunks are stored as plain text in `nodes.json` for BM25

**Retrieval (`agent/rag.py`):**
- Hybrid: FAISS top-4 (semantic) + BM25 top-3 (keyword), deduplicated to ≤5 passages
- Triggered on every user turn with >6 words or containing `?`; short utterances skip retrieval to reduce latency
- For the `get_exercise_form_cues` tool call, retrieval is run with a focused query (`"{exercise} technique execution form"`) to ensure precise cue lookup

**Injection:** Retrieved passages are injected as an assistant-role context message before the LLM generates its response. The injection includes a reminder to still call tools for exercise form and motivation questions, so RAG context does not suppress tool calls.

**Index storage:** The pre-built `agent/storage/` directory is committed to the repo. The agent loads the index at startup and never re-indexes at runtime.

---

## Tools

| Tool | When called | What it does |
|------|-------------|--------------|
| `get_exercise_form_cues` | Any exercise form or technique question | Runs targeted RAG retrieval and returns cues from the Encyclopedia |
| `generate_workout_plan` | Training plan request | Returns a pre-built weekly plan for the user's goal, experience, and schedule |
| `get_arnold_quote` | Motivation, doubt, or encouragement | Returns an Arnold quote matched to the desired tone |

---

## Frameworks & Tools Used

| Layer | Choice |
|-------|--------|
| Voice agent framework | LiveKit Agents v1.x (Python) |
| STT | Deepgram Nova-3 |
| LLM | OpenAI GPT-4.1-mini |
| TTS | ElevenLabs `eleven_turbo_v2_5` |
| VAD | Silero |
| RAG framework | LlamaIndex 0.10.x |
| Vector store | FAISS (`faiss-cpu`) |
| Keyword retrieval | `bm25s` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Frontend | Next.js 15, LiveKit Components React |
| Frontend hosting | Vercel |
| Agent hosting | AWS EC2 `t3.small` (Docker) |

---

## Setup

### Prerequisites
- Python 3.11, Node.js 18+
- API keys: LiveKit Cloud, OpenAI, Deepgram, ElevenLabs

### Run the agent locally
```bash
cd agent
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in all keys
python agent.py start
```

### Run the frontend locally
```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in LIVEKIT_* keys
npm run dev   # http://localhost:3000
```

With both running, open `http://localhost:3000` and click **BEGIN SESSION**.

### Run tests
```bash
cd agent && pytest tests/ -v
cd frontend && npm test
```

---

## Design Decisions & Assumptions

**RAG chunking:** Chunks are ~512 tokens with 50-token overlap. The Encyclopedia is dense and exercise-specific, so smaller chunks produce more precise retrieval hits than page-level summaries. A proper semantic splitter wasn't used — simple size-based splitting was sufficient given how the book is structured (one exercise per section).

**Hybrid retrieval:** Pure vector search misses exact exercise names (e.g. "preacher curl") that may not be semantically close to the query embedding. BM25 catches these. The combination reliably handles both vague ("how do I build my chest") and precise ("how do I do a concentration curl") queries.

**BM25 directly:** `llama-index-retrievers-bm25` has import conflicts with `llama-index-core` 0.10.x. The `bm25s` library is used directly instead, with the same node corpus.

**Preemptive generation disabled:** LiveKit Agents can start generating a response before `on_user_turn_completed` finishes. When RAG modifies the context mid-generation, the preemptive output is discarded and the LLM regenerates — and in practice it skipped tool calls on the second pass. Disabling preemptive generation eliminates this race.

**gpt-4.1-mini:** Used for cost and latency. It is less reliable at function calling than `gpt-4o` or `gpt-4.1`, so the system prompt and tool docstrings are written to be as explicit as possible about when tools must be called.

**Hosting:** The agent runs as a Docker container on a single `t3.small` (2 GB RAM). The FAISS index takes ~800 MB at load time, so `t2.micro` (1 GB) is not sufficient. The `--restart unless-stopped` Docker flag keeps the worker alive across reboots. The agent connects outbound to LiveKit Cloud on startup — no inbound ports needed on the EC2 instance beyond SSH.

**Multi-user:** Each browser session generates a unique room name and participant identity at token-creation time (`arnold-${Date.now()}`). LiveKit Cloud dispatches a fresh agent job per room, so concurrent users each get their own isolated session.

**Tab-close / disconnect:** LiveKit Cloud detects when the user's participant disconnects (tab close, network loss). The agent worker receives a room-empty signal and exits cleanly. Sessions do not linger.
