import asyncio
import logging

import httpx

from src.prompt_builder import build_messages

logger = logging.getLogger(__name__)

_RETRY_COUNT = 3
_RETRY_BASE_DELAY = 2.0  # seconds


async def call_llm(messages: list[dict], config: dict) -> str:
    """Call the OpenAI-compatible chat completions endpoint.

    Retries up to _RETRY_COUNT times with exponential backoff. Returns a
    placeholder error string if all retries are exhausted.
    """
    api_cfg = config["api"]
    url = f"{api_cfg['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_cfg["model"],
        "messages": messages,
        "max_tokens": api_cfg["max_tokens"],
        "temperature": api_cfg["temperature"],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(1, _RETRY_COUNT + 1):
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == _RETRY_COUNT:
                    logger.error(
                        f"LLM call failed after {_RETRY_COUNT} retries: {e}"
                    )
                    return f"[ERROR: Failed to process this batch after {_RETRY_COUNT} retries]"
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"LLM call attempt {attempt} failed ({e}). "
                    f"Retrying in {delay:.0f}s..."
                )
                await asyncio.sleep(delay)

    # Unreachable, but satisfies type checkers
    return f"[ERROR: Failed to process this batch after {_RETRY_COUNT} retries]"


async def process_batches(
    batches: list[list[dict]],
    research_angle: str,
    config: dict,
) -> list[str]:
    """Process all batches concurrently, respecting the semaphore limit.

    Returns responses in the same order as the input batches.
    """
    semaphore = asyncio.Semaphore(config["api"]["max_concurrent_requests"])
    total = len(batches)

    async def process_one(index: int, batch: list[dict]) -> tuple[int, str]:
        async with semaphore:
            logger.info(f"Processing batch {index + 1}/{total}...")
            messages = build_messages(research_angle, batch)
            result = await call_llm(messages, config)
            return index, result

    tasks = [process_one(i, batch) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks)

    # Re-sort by original index to preserve order
    ordered = sorted(results, key=lambda x: x[0])
    return [response for _, response in ordered]
