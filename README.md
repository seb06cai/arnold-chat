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

## Design Decisions & Assumptions

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
