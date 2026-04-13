import logging

logger = logging.getLogger(__name__)


def _estimate_tokens(paper: dict) -> int:
    """Rough token estimate: total character count across all pages divided by 4."""
    total_chars = sum(len(p["text"]) for p in paper["pages"])
    return total_chars // 4


def create_batches(
    papers: list[dict],
    max_tokens: int,
    max_papers: int,
) -> list[list[dict]]:
    """Group papers into batches that fit within token and paper count limits.

    A single paper that exceeds max_tokens is placed in its own batch with a
    warning logged.
    """
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_tokens = 0

    for paper in papers:
        paper_tokens = _estimate_tokens(paper)

        if paper_tokens > max_tokens:
            logger.warning(
                f"{paper['filename']} alone exceeds the token limit "
                f"({paper_tokens} estimated tokens > {max_tokens}). "
                "It will be sent in its own batch and may be truncated by the model."
            )
            # Flush current batch first if non-empty
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            batches.append([paper])
            continue

        would_exceed_tokens = (current_tokens + paper_tokens) > max_tokens
        would_exceed_papers = len(current_batch) >= max_papers

        if current_batch and (would_exceed_tokens or would_exceed_papers):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(paper)
        current_tokens += paper_tokens

    if current_batch:
        batches.append(current_batch)

    return batches
