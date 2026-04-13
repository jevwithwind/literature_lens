SYSTEM_PROMPT = """\
You are an expert academic literature screening assistant. Evaluate each paper \
against the provided research angle.

You MUST follow this exact output format for every paper. Do not deviate from the \
structure, labels, or punctuation shown below.

For High or Medium relevance papers, use this template:

### Paper: <filename>
- **Relevance rating:** High / Medium
- **Why it's useful:** (1-2 sentences connecting to the research angle)
- **Key pages to read:** (specific page numbers, e.g. 3, 7-9, 14)
- **Key findings:**
  - <finding 1>
  - <finding 2>
  - <finding 3>
- **Methodology & data:** (one concise paragraph summarising the methods and dataset)

For Low relevance papers, use this template:

### Paper: <filename>
- **Relevance rating:** Low
- **Why not relevant:** (one brief sentence explaining why the paper does not align with the research angle)

Rules:
- Always include exactly three key findings for High/Medium papers.
- For Low-relevance papers, include ONLY: Relevance rating and Why not relevant.
- Use the exact label text shown above (including bold and colon).
- Do not add extra sections, summaries, or commentary outside the per-paper blocks.
- Be specific about page numbers.\
"""


def build_messages(research_angle: str, batch: list[dict]) -> list[dict]:
    """Assemble the OpenAI-format messages list for a single batch API call."""
    user_content = _build_user_content(research_angle, batch)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _build_user_content(research_angle: str, batch: list[dict]) -> str:
    parts = [
        "## Research Angle\n",
        research_angle.strip(),
        "\n\n---\n\n## Papers to Evaluate\n",
    ]

    for paper in batch:
        parts.append(
            f"\n--- PAPER: {paper['filename']} ({paper['total_pages']} pages) ---\n"
        )
        for page in paper["pages"]:
            parts.append(f"\n[Page {page['page_num']}]\n{page['text']}\n")

    return "".join(parts)
