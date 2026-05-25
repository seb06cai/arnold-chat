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

### Why Hybrid Retrieval (FAISS + BM25)

Pure vector search fails on a domain like bodybuilding because exercise names that are semantically similar refer to completely different movements — "preacher curl" and "concentration curl" land close in embedding space but target different heads of the bicep with different form cues. A user asking about one would get passages about both, which is wrong.

- **FAISS (semantic, top-4)** handles intent-driven queries well: "how do I build a bigger chest" correctly surfaces bench press, flyes, and dips even though the user never named them.
- **BM25 (keyword, top-3)** anchors retrieval to exact terminology: when someone says "preacher curl," the keyword match ensures the preacher curl section ranks highest regardless of embedding similarity to related exercises.
- Results are deduplicated down to **≤5 passages** to stay within a context budget that keeps latency low for a real-time voice agent — the LLM can't spend seconds processing a wall of context when someone is waiting for a spoken reply.

### Chunking Strategy

The source PDF is Arnold's *Encyclopedia of Modern Bodybuilding* — a 700+ page book organized by body part and exercise, with each section roughly self-contained. Fixed-size chunks (~512 tokens, 50-token overlap) align naturally with this structure because most exercise entries fit within one or two chunks.

- Semantic or recursive chunking would add complexity without a clear payoff here: the text is already well-structured, and the hybrid retrieval layer compensates for any cases where a chunk boundary splits a section mid-thought.
- The 50-token overlap ensures that sentences at chunk boundaries are never orphaned — if a form cue spans two chunks, at least one chunk captures the full sentence.

### Agent Pipeline Design

The voice pipeline chains four services in sequence: **Deepgram STT → GPT-4.1-mini → ElevenLabs TTS**, with **Silero VAD** for turn detection. Each was chosen for a specific reason:

- **Deepgram Nova-3** for STT because it has strong accuracy on gym/fitness vocabulary out of the box and streams partial transcripts, which feeds into the live transcript UI.
- **GPT-4.1-mini** as the LLM because it balances quality with latency — fast enough for real-time conversation, capable enough to follow Arnold's persona instructions and make tool calls reliably.
- **ElevenLabs Turbo v2.5** for TTS because it supports low-latency streaming and has a voice library with a close match for Arnold's cadence and tone.
- **Silero VAD** because LiveKit's agent framework integrates it natively for turn detection, and it handles the pauses and breathing patterns of natural speech well.

RAG injection happens between STT and LLM: once the user's turn is transcribed, the agent runs hybrid retrieval and injects matched passages as a context message before the LLM generates its response. Preemptive generation is disabled to ensure the LLM always sees the full RAG context before responding.

### Hosting Architecture

- **Frontend on Vercel** — zero-config deployment for the Next.js app, with the `/api/token` route running as a serverless function to mint LiveKit JWTs.
- **Agent on AWS EC2 (Docker)** — the Python agent worker needs a persistent process to stay registered with LiveKit Cloud as a worker, which rules out serverless. A single EC2 instance running the agent in Docker keeps it simple and always available for room dispatch.
- **LiveKit Cloud** as the media server — handles all WebRTC complexity (STUN/TURN, codec negotiation, room state) so the agent only needs to implement the conversation logic.

### Limitations & Future Improvements

- **Transcript streaming:** Currently the transcript updates per-utterance rather than word-by-word. Word-level streaming would make the UI feel more responsive and natural during longer Arnold monologues.
- **Chunk strategy:** A semantic chunking approach that respects section headers in the book could improve retrieval precision for passages that span multiple exercises in a single section (e.g., supersets).
- **Reranking:** Adding a cross-encoder reranker after the hybrid merge would let the pipeline retrieve more candidates and then pick the truly best passages, improving answer quality on ambiguous queries.
- **Evaluation:** There is no automated retrieval evaluation pipeline — adding one with a set of ground-truth question/passage pairs would make it possible to quantify the impact of changes to chunking, embedding models, or retrieval parameters.
