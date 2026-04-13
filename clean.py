#!/usr/bin/env python
"""Delete all PDF files in the intake folder."""

import logging
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_config()
    intake_dir = Path(config["paths"]["intake_dir"])

    if not intake_dir.exists():
        logger.info(f"Intake directory does not exist: {intake_dir}")
        return

    pdf_files = sorted(intake_dir.glob("*.pdf"))

    if not pdf_files:
        logger.info("No PDFs found in intake/. Nothing to clean.")
        return

    for pdf_path in pdf_files:
        pdf_path.unlink()
        logger.info(f"Deleted: {pdf_path.name}")

    logger.info(f"Cleaned {len(pdf_files)} PDF(s) from {intake_dir}.")


if __name__ == "__main__":
    main()
