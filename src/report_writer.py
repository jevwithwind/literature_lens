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


def _build_summary_table(responses: list[str]) -> str:
    """Parse LLM responses to build a Markdown summary table.

    Falls back to a note if parsing yields no rows.
    """
    header = "| # | Paper | Relevance | Key Pages |\n|---|-------|-----------|-----------|"
    rows: list[str] = []

    # Patterns to pull paper name, relevance, and key pages from LLM output.
    # The LLM is prompted to follow a consistent structure, so these patterns
    # are intentionally flexible to handle minor formatting variation.
    paper_pattern = re.compile(
        r"(?:PAPER:|##\s*Paper[:\s]+|###\s*)([^\n]+\.pdf)", re.IGNORECASE
    )
    relevance_pattern = re.compile(
        r"Relevance(?:\s+rating)?[:\s]+\*{0,2}(High|Medium|Low)\*{0,2}",
        re.IGNORECASE,
    )
    pages_pattern = re.compile(
        r"Key\s+pages?(?:\s+to\s+read)?[:\s]+([^\n]+)", re.IGNORECASE
    )

    row_num = 1
    for response in responses:
        paper_names = paper_pattern.findall(response)
        relevances = relevance_pattern.findall(response)
        key_pages_list = pages_pattern.findall(response)

        # Zip found values; use placeholders for missing fields
        max_entries = max(len(paper_names), len(relevances), len(key_pages_list), 1)
        for i in range(max_entries):
            name = paper_names[i].strip() if i < len(paper_names) else "-"
            relevance = relevances[i].strip() if i < len(relevances) else "-"
            pages = key_pages_list[i].strip() if i < len(key_pages_list) else "-"
            # Guard against accidentally empty rows with no real data
            if name == "-" and relevance == "-":
                continue
            rows.append(f"| {row_num} | {name} | {relevance} | {pages} |")  # noqa: E501
            row_num += 1

    if not rows:
        return (
            f"{header}\n"
            "| - | *(Could not parse summary - see Detailed Evaluations below)* | - | - |"
        )

    return header + "\n" + "\n".join(rows)


def _build_detailed_section(responses: list[str]) -> str:
    """Concatenate batch responses separated by horizontal rules."""
    return "\n\n---\n\n".join(response.strip() for response in responses)
