"""Bootstrap lightweight Client 1 data-quality assets for the current architecture."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


QUALITY_ROOT = Path(__file__).resolve().parent
CHECKPOINTS_DIR = QUALITY_ROOT / "checkpoints"
DATA_DOCS_DIR = QUALITY_ROOT / "data_docs"
ARTIFACTS_DIR = QUALITY_ROOT / "artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap Client 1 quality-check assets."
    )
    parser.add_argument(
        "--layers",
        default="raw",
        choices=["raw", "all"],
        help="Scope of quality assets to prepare.",
    )
    return parser.parse_args()


def ensure_directories() -> None:
    for directory in (CHECKPOINTS_DIR, DATA_DOCS_DIR, ARTIFACTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def write_checkpoint_manifest(layers: str) -> list[str]:
    checkpoints = ["raw_lakehouse_quality_checkpoint"]
    if layers == "all":
        checkpoints.append("platform_readiness_checkpoint")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": layers,
        "checkpoints": checkpoints,
    }
    (CHECKPOINTS_DIR / "checkpoint_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return checkpoints


def write_data_docs_placeholder(checkpoints: list[str]) -> None:
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustomerDNA Quality Docs</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
    h1 {{ color: #1f2937; }}
    code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>CustomerDNA Client 1 Lakehouse Quality Assets</h1>
  <p>This environment uses lightweight bootstrap artifacts for the current distributed lakehouse setup.</p>
  <p>Available checkpoints:</p>
  <ul>
    {''.join(f'<li><code>{checkpoint}</code></li>' for checkpoint in checkpoints)}
  </ul>
</body>
</html>
"""
    (DATA_DOCS_DIR / "index.html").write_text(html_content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_directories()
    checkpoints = write_checkpoint_manifest(args.layers)
    write_data_docs_placeholder(checkpoints)

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 QUALITY BOOTSTRAP")
    print("=" * 80)
    print(f"Scope: {args.layers}")
    print("Prepared checkpoints:")
    for checkpoint in checkpoints:
        print(f"  - {checkpoint}")
    print(f"Data docs placeholder: {DATA_DOCS_DIR / 'index.html'}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
