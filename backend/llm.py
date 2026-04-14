import os
import asyncio
import time
import logging
from google import genai
from google.genai import types
logger = logging.getLogger(__name__)
_api_lock = asyncio.Lock()
_last_request_time = 0.0
async def _wait_for_rate_limit():
    global _last_request_time
    async with _api_lock:
        now = time.time()
        elapsed = now - _last_request_time
        delay = max(0.0, 6.5 - elapsed)
        if delay > 0:
            await asyncio.sleep(delay)
        _last_request_time = time.time()
def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Get a FREE key at https://aistudio.google.com/app/apikey "
            "and add it to backend/.env as: GEMINI_API_KEY=your-key-here"
        )
    return genai.Client(api_key=api_key)
DEFAULT_MODEL = "gemini-2.0-flash"
FALLBACK_MODEL = "gemini-2.0-flash-lite"
async def gemini_generate(
    prompt: str,
    system_prompt: str = "",
    model_name: str = DEFAULT_MODEL,
    max_output_tokens: int = 8192,
    temperature: float = 0.7,
    max_retries: int = 5,
) -> str:
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
    for attempt in range(max_retries):
        await _wait_for_rate_limit()
        try:
            result = await loop.run_in_executor(None, lambda: _blocking_call(model_name))
            return result.strip() if result else ""
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                wait_time = min(2 ** attempt * 5, 60)  
                logger.warning(
                    f"Gemini 429 on attempt {attempt + 1}/{max_retries}. "
                    f"Retrying in {wait_time}s..."
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
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
            raise
    return ""