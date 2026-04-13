import asyncio
import logging
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.batcher import create_batches
from src.llm_client import process_batches
from src.pdf_reader import extract_papers
from src.report_writer import write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_research_angle(prompt_file: str) -> str:
    path = Path(prompt_file)
    if not path.exists():
        raise FileNotFoundError(f"Research angle file not found: {prompt_file}")
    return path.read_text(encoding="utf-8")


async def run_pipeline(config: dict, research_angle: str) -> None:
    intake_dir = config["paths"]["intake_dir"]
    logger.info(f"Scanning for PDFs in {intake_dir}...")

    papers = extract_papers(intake_dir)

    if not papers:
        logger.info("No PDFs found in intake/. Drop some PDFs in and re-run.")
        print("\nNo PDFs found. Exiting.")
        return

    successful = [p for p in papers if p["extraction_success"]]
    failed = [p for p in papers if not p["extraction_success"]]

    if failed:
        logger.warning(
            f"{len(failed)} file(s) could not be extracted and will be skipped: "
            + ", ".join(p["filename"] for p in failed)
        )

    if not successful:
        logger.error("No papers could be extracted. Exiting.")
        print("\nAll PDF extractions failed. Check the logs above.")
        return

    logger.info(f"Extracted {len(successful)} paper(s) successfully.")

    batches = create_batches(
        papers=successful,
        max_tokens=config["batch"]["max_tokens_per_batch"],
        max_papers=config["batch"]["max_papers_per_batch"],
    )
    logger.info(f"Created {len(batches)} batch(es).")

    responses = await process_batches(batches, research_angle, config)

    report_path = write_report(
        responses=responses,
        research_angle=research_angle,
        paper_count=len(successful),
        config=config,
    )

    print(f"\nDone. {len(successful)} paper(s) screened.")
    print(f"Report written to: {report_path}")


def main() -> None:
    try:
        load_dotenv()

        config = load_config("config.yaml")

        base_url_env = config["api"]["base_url_env"]
        base_url = os.getenv(base_url_env)
        if not base_url:
            print(
                f"Error: Environment variable '{base_url_env}' is not set. "
                "Add it to your .env file (e.g. OPENAI_BASE_URL=https://your-endpoint/v1)."
            )
            sys.exit(1)
        config["api"]["base_url"] = base_url

        api_key_env = config["api"]["api_key_env"]
        api_key = os.getenv(api_key_env)
        if not api_key:
            print(
                f"Error: Environment variable '{api_key_env}' is not set. "
                "Add it to your .env file."
            )
            sys.exit(1)
        config["api"]["api_key"] = api_key

        model_env = config["api"]["model_env"]
        model = os.getenv(model_env)
        if not model:
            print(
                f"Error: Environment variable '{model_env}' is not set. "
                "Add it to your .env file (e.g. LLM_MODEL=qwen3.6-plus)."
            )
            sys.exit(1)
        config["api"]["model"] = model

        research_angle = load_research_angle(config["paths"]["prompt_file"])

        asyncio.run(run_pipeline(config, research_angle))

    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
