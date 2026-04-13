SYSTEM_PROMPT = """\
You are an expert academic literature screening assistant. Evaluate each paper \
against the provided research angle.

For papers rated High or Medium relevance, provide all of the following:
- Relevance rating (High / Medium / Low)
- Why it's useful (1-2 sentences connecting to the research angle)
- Key pages to read (specific page numbers)
- Key findings (exactly three bullet points of the most important findings)
- Methodology & data (one concise paragraph summarising the methods used and \
the dataset or data sources the paper relies on)

For papers rated Low relevance, provide only:
- Relevance rating (Low)
- Key findings (exactly three bullet points of the most important findings)

Be specific about page numbers.\
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
