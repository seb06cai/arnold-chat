from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    llm,
)
from livekit.plugins import deepgram, elevenlabs, openai, silero

import tools as arnold_tools
from rag import load_retriever, retrieve

logger = logging.getLogger("arnold-coach")

SYSTEM_PROMPT = """You are Arnold Schwarzenegger coaching users from Gold's Gym Venice Beach, 1977.

Your Encyclopedia: You wrote The Encyclopedia of Modern Bodybuilding and it contains your life's work on exercise technique. Any time a user asks how to perform, do, execute, or demonstrate any exercise — curl, squat, press, deadlift, row, pull-up, or anything else — you say "Let me check ze Encyclopedia..." and call get_exercise_form_cues immediately. You do this before saying anything else about the exercise. Every exercise question. Every time. No exceptions.

Your voice: 2-3 sentences maximum per response. Short and punchy. Austrian phonetics — "ze", "vhy", "vant", "zat" — 1-2 per response, not every word. Personal anecdotes natural: "Ven I vas preparing for ze 1975 Olympia...", "Franco and I trained zis vay..." No markdown, no bullet points, no lists. Never break character.

Your other tools — always use them:
- Training plan or program request → call generate_workout_plan, speak the result naturally
- Motivation, a quote, encouragement, or the user expresses doubt or laziness → call get_arnold_quote, never improvise a quote"""

GREETING = "Velcome to ze iron temple. I am Arnold. Vhat do you vant to build today?"

_rag_available: bool = False


def _load_rag_state() -> None:
    global _rag_available
    try:
        load_retriever()
        _rag_available = True
        logger.info("RAG retriever loaded successfully")
    except Exception as exc:
        logger.warning("RAG retriever failed to load (will skip injection): %s", exc)
        _rag_available = False


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class ArnoldAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            stt=deepgram.STT(
                model="nova-3",
                api_key=_require_env("DEEPGRAM_API_KEY"),
            ),
            llm=openai.LLM(
                model="gpt-4.1-mini",
                api_key=_require_env("OPENAI_API_KEY"),
            ),
            tts=elevenlabs.TTS(
                voice_id=os.environ.get("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJgB"),
                model="eleven_turbo_v2_5",
                api_key=_require_env("ELEVEN_API_KEY"),
            ),
            vad=silero.VAD.load(min_silence_duration=0.8),
        )

    async def on_enter(self) -> None:
        self.session.say(GREETING)

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        text = ""
        if isinstance(new_message.content, str):
            text = new_message.content
        elif isinstance(new_message.content, list):
            for part in new_message.content:
                if isinstance(part, str):
                    text += part

        if len(text.split()) <= 6 and "?" not in text:
            return

        if not _rag_available:
            return

        try:
            passages = retrieve(load_retriever(), text)
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            return

        if not passages:
            return

        context_block = "\n\n---\n".join(passages[:3])
        injection = (
            "[Encyclopedia of Modern Bodybuilding — background context. "
            "For exercise form or technique questions, still call get_exercise_form_cues. "
            "For motivation, quotes, or encouragement, still call get_arnold_quote. "
            "Do not answer those from this background alone.]\n"
            + context_block
        )
        turn_ctx.add_message(role="assistant", content=injection)

    @function_tool
    async def generate_workout_plan(
        self,
        context: RunContext,
        goal: str,
        experience_level: str,
        days_per_week: int,
    ) -> str:
        """Generate a personalized weekly workout plan.

        Args:
            goal: Fitness goal — strength, hypertrophy, endurance, or weight_loss.
            experience_level: User experience level — beginner, intermediate, or advanced.
            days_per_week: Number of training days per week, 1 to 6.
        """
        return arnold_tools.generate_workout_plan(goal, experience_level, days_per_week)

    @function_tool
    async def get_arnold_quote(
        self,
        context: RunContext,
        mood: str,
    ) -> str:
        """Get an Arnold Schwarzenegger quote for motivation.

        Args:
            mood: Desired tone — motivational, tough_love, or philosophical.
        """
        return arnold_tools.get_arnold_quote(mood)

    @function_tool
    async def get_exercise_form_cues(
        self,
        context: RunContext,
        exercise: str,
    ) -> str:
        """MUST be called for any exercise form, technique, or how-to question. Looks up the exercise in the Arnold Encyclopedia and returns authoritative form cues. Call this before saying anything about how to perform the exercise.

        Args:
            exercise: Name of the exercise to look up (e.g. "barbell curl", "squat", "deadlift").
        """
        if not _rag_available:
            return (
                "I cannot access ze Encyclopedia right now. "
                "But remember: full range of motion, feel ze muscle, control ze weight."
            )
        try:
            retriever = load_retriever()
            passages = retrieve(retriever, f"{exercise} technique execution form")
            if not passages:
                passages = retrieve(retriever, exercise)
            if not passages:
                return (
                    f"Ze Encyclopedia does not have specific notes on {exercise}. "
                    "Focus on full range of motion and feeling ze contraction."
                )
            return "\n\n".join(passages[:2])
        except Exception as exc:
            logger.warning("RAG form lookup failed: %s", exc)
            return f"Train {exercise} with full range of motion and controlled negatives. Zat is how I built my physique."


async def entrypoint(ctx: JobContext) -> None:
    _load_rag_state()  # must run in the subprocess, not the parent process
    await ctx.connect()
    session = AgentSession(
        turn_handling={
            "preemptive_generation": {"enabled": False},
            "interruption": {
                "min_duration": 0.8,
                "min_words": 3,
            },
        },
    )
    await session.start(ArnoldAgent(), room=ctx.room)


if __name__ == "__main__":
    _load_rag_state()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="arnold-coach",
        )
    )
