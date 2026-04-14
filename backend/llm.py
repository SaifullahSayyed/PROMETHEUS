"""
Shared Gemini client for all PROMETHEUS agents.
Uses google-genai (the current, non-deprecated SDK) — completely FREE tier.
Get your key: https://aistudio.google.com/app/apikey  (sign in with Google, 30 seconds)

Includes automatic exponential-backoff retry on 429 RESOURCE_EXHAUSTED errors.
"""
import os
import asyncio
import time
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent Gemini API calls (free tier: 15 RPM)
# Allows up to 3 parallel calls — enough for our architecture without hitting 429s
_api_semaphore = asyncio.Semaphore(2)


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Get a FREE key at https://aistudio.google.com/app/apikey "
            "and add it to backend/.env as: GEMINI_API_KEY=your-key-here"
        )
    return genai.Client(api_key=api_key)


# Gemini 2.0 Flash — free tier, fast, excellent quality for all agent tasks
DEFAULT_MODEL = "gemini-2.0-flash"

# Fallback model if flash hits limits
FALLBACK_MODEL = "gemini-2.0-flash-lite"


async def gemini_generate(
    prompt: str,
    system_prompt: str = "",
    model_name: str = DEFAULT_MODEL,
    max_output_tokens: int = 8192,
    temperature: float = 0.7,
    max_retries: int = 5,
) -> str:
    """
    Async wrapper around the Gemini generate_content call.
    - Runs the blocking SDK call in a thread pool to avoid blocking the event loop.
    - Limits concurrent API calls via semaphore (prevents 429s on free tier).
    - Retries with exponential backoff on 429 RESOURCE_EXHAUSTED errors.
    """
    client = _get_client()

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_prompt if system_prompt else None,
    )

    loop = asyncio.get_event_loop()

    def _blocking_call(model: str) -> str:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        return response.text

    # Rate-limited execution with exponential backoff
    async with _api_semaphore:
        # Ensure we don't exceed the 15 RPM limit (4 seconds per request)
        await asyncio.sleep(4)
        
        for attempt in range(max_retries):
            try:
                result = await loop.run_in_executor(None, lambda: _blocking_call(model_name))
                return result.strip() if result else ""
            except Exception as e:
                err_str = str(e)

                # Handle 429 Resource Exhausted
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    wait_time = min(2 ** attempt * 5, 60)  # 5s, 10s, 20s, 40s, 60s
                    logger.warning(
                        f"Gemini 429 on attempt {attempt + 1}/{max_retries}. "
                        f"Retrying in {wait_time}s..."
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                        # Try fallback model on later attempts
                        if attempt >= 2 and model_name != FALLBACK_MODEL:
                            logger.info(f"Switching to fallback model: {FALLBACK_MODEL}")
                            model_name = FALLBACK_MODEL
                        continue
                    else:
                        raise RuntimeError(
                            f"Gemini API quota exhausted after {max_retries} retries. "
                            "Please wait 1 minute and try again, or check your API quotas at "
                            "https://aistudio.google.com/app/apikey"
                        ) from e

                # Handle other errors — fail immediately
                raise

    return ""
