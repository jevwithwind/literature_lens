import re
from datetime import datetime
from pathlib import Path


def write_report(
    responses: list[str],
    research_angle: str,
    paper_count: int,
    config: dict,
) -> str:
    """Aggregate batch responses into a single Markdown report.

    Returns the path of the written report file.
    """
    now = datetime.now()
    timestamp_display = now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = now.strftime("%Y%m%d_%H%M%S")

    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"report_{timestamp_file}.md"

    summary_table = _build_summary_table(responses)
    detailed_section = _build_detailed_section(responses)

    angle_blockquote = "\n".join(
        f"> {line}" for line in research_angle.strip().splitlines()
    )

    report = f"""# Literature Lens Report
**Generated**: {timestamp_display}
**Papers Screened**: {paper_count}

## Research Angle
{angle_blockquote}

## Summary Table
{summary_table}

## Detailed Evaluations

{detailed_section}
"""

    report_path.write_text(report, encoding="utf-8")
    return str(report_path)


def _parse_papers(responses: list[str]) -> list[dict]:
    """Parse all papers from LLM responses into structured dicts.

    Each dict contains: filename, relevance, reasoning, and raw text.
    """
    paper_pattern = re.compile(
        r"###\s*Paper:\s*`?([^\n`]+\.pdf)", re.IGNORECASE,
    )
    relevance_pattern = re.compile(
        r"\*\*Relevance rating:\*\*\s*(High|Medium|Low)",
        re.IGNORECASE,
    )
    reasoning_pattern = re.compile(
        r"\*\*Why it's useful:\*\*\s*(.+)", re.IGNORECASE,
    )

    papers = []
    for response in responses:
        # Split response into individual paper blocks
        paper_blocks = re.split(r"(?=###\s+Paper:)", response)
        for block in paper_blocks:
            block = block.strip()
            if not block:
                continue

            name_match = paper_pattern.search(block)
            rel_match = relevance_pattern.search(block)
            reason_match = reasoning_pattern.search(block)

            if not name_match:
                continue

            filename = name_match.group(1).strip()
            relevance = rel_match.group(1).strip() if rel_match else "Low"
            reasoning = reason_match.group(1).strip() if reason_match else ""

            papers.append({
                "filename": filename,
                "relevance": relevance,
                "reasoning": reasoning,
                "raw": block,
            })

    return papers


def _build_summary_table(responses: list[str]) -> str:
    """Build a summary table with High/Medium papers first, then Low.

    Columns: #, Paper, Reasoning
    """
    header = "| # | Paper | Reasoning |\n|---|-------|-----------|"
    papers = _parse_papers(responses)

    # Sort: High/Medium first, then Low
    relevance_order = {"High": 0, "Medium": 1, "Low": 2}
    papers.sort(key=lambda p: relevance_order.get(p["relevance"], 3))

    rows = []
    for i, paper in enumerate(papers, 1):
        reasoning = paper["reasoning"] if paper["relevance"] in ("High", "Medium") else "-"
        rows.append(f"| {i} | {paper['filename']} | {reasoning} |")

    if not rows:
        return (
            f"{header}\n"
            "| - | *(Could not parse summary - see Detailed Evaluations below)* | - |"
        )

    return header + "\n" + "\n".join(rows)


def _build_detailed_section(responses: list[str]) -> str:
    """Concatenate paper evaluations, sorted with High/Medium first, then Low.

    Normalizes paper headers to a consistent format.
    """
    papers = _parse_papers(responses)

    # Sort: High/Medium first, then Low
    relevance_order = {"High": 0, "Medium": 1, "Low": 2}
    papers.sort(key=lambda p: relevance_order.get(p["relevance"], 3))

    # Normalize headers in raw text
    header_pattern = re.compile(
        r"^(#{1,3}\s*)?(?:\*\*)?PAPER[:\s]+\*{0,2}\s*(.+?\.pdf)\s*\*{0,2}\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    sections = []
    for paper in papers:
        cleaned = header_pattern.sub(r"### Paper: \2", paper["raw"])
        sections.append(cleaned.strip())

    return "\n\n---\n\n".join(sections)
