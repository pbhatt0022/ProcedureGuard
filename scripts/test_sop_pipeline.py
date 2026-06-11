"""
Smoke test for the SOP extraction pipeline.

Tests Document Intelligence (Layout model) against a real SOP PDF without
needing the full pipeline. Accepts a local file or a Blob SAS URL.

Usage:
    # Local fixture, first 15 pages (recommended — full manual is 200+ pages)
    python scripts/test_sop_pipeline.py --file tests/fixtures/prusa_mk3s_plus_assembly.pdf --pages 1-15

    # Blob Storage SAS URL
    python scripts/test_sop_pipeline.py --url "https://your-sas-url..." --pages 1-15

    # Save the Steps JSON for inspection / downstream testing
    python scripts/test_sop_pipeline.py --file ... --pages 1-15 --out steps.json

What to look for in the output:
    - If analysis fails with 401/403: check AZURE_DOCUMENT_INTELLIGENCE_KEY in .env
    - If 0 steps extracted: page range may cover only cover/TOC pages — widen it
    - Garbled/fragmented descriptions: parsing heuristic issue — log in KNOWN_ISSUES.md

Owner: Person A (SOP pipeline)
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so `config` and `src` are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 stdout so emoji in print statements work on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_FIXTURE = "tests/fixtures/prusa_mk3s_plus_assembly.pdf"


def parse_args():
    parser = argparse.ArgumentParser(description="ProcedureGuard SOP pipeline smoke test")
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--file",
        default=DEFAULT_FIXTURE,
        help=f"Local path to an SOP PDF (default: {DEFAULT_FIXTURE})",
    )
    source.add_argument(
        "--url",
        help="Blob SAS URL or public HTTPS URL to an SOP PDF (overrides --file)",
    )
    parser.add_argument(
        "--pages",
        default=None,
        help='Page range, e.g. "1-15". Strongly recommended for the 200+ page Prusa manual.',
    )
    parser.add_argument(
        "--run-id",
        default="run-sop-smoke-001",
        help="run_id for this test run (default: run-sop-smoke-001)",
    )
    parser.add_argument(
        "--granularity",
        choices=["paragraph", "section"],
        default="paragraph",
        help='Step granularity. Use "section" for instruction-manual style docs '
             'like the Prusa manual (one step per "STEP N" heading).',
    )
    parser.add_argument(
        "--out",
        help="Optional path to save the extracted Steps JSON",
    )
    parser.add_argument(
        "--max-print",
        type=int,
        default=10,
        help="Max steps to print in the summary table (default: 10)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    from config import cfg
    from src.ingestion.sop_extractor import extract_sop_steps

    source = args.url or args.file
    if not args.url and not Path(source).exists():
        print(f"❌ Fixture not found: {source}")
        print("   Download the Prusa MK3S+ assembly manual PDF to tests/fixtures/ first.")
        sys.exit(1)

    print("ProcedureGuard — SOP Pipeline Smoke Test")
    print(f"Endpoint: {cfg.doc_intelligence_endpoint}")
    print(f"Source  : {source if args.url is None else source[:80] + '...'}")
    print(f"Pages   : {args.pages or 'all (warning: slow for large manuals)'}")
    print(f"Granularity: {args.granularity}")
    print(f"run_id  : {args.run_id}")

    print("\nAnalyzing with Layout model (this can take 30s–3min)...")
    started = time.monotonic()
    try:
        steps_json = extract_sop_steps(
            source, args.run_id, pages=args.pages, granularity=args.granularity
        )
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        print("\nCommon causes:")
        print("  - Missing/wrong AZURE_DOCUMENT_INTELLIGENCE_KEY or _ENDPOINT in .env")
        print("  - SAS URL expired (regenerate with az storage blob generate-sas)")
        print("  - Page range outside document bounds")
        sys.exit(1)
    elapsed = time.monotonic() - started

    print(f"\n✅ Extraction complete in {elapsed:.0f}s — {steps_json['total_steps']} step(s)")

    # Summary table
    print("\n" + "=" * 60)
    print(f"FIRST {min(args.max_print, steps_json['total_steps'])} STEPS")
    print("=" * 60)
    for step in steps_json["steps"][: args.max_print]:
        desc = step["description"][:70].replace("\n", " ")
        dur = f" [{step['expected_duration_seconds']}s]" if step["expected_duration_seconds"] else ""
        figs = f" ({len(step['visual_references'])} fig)" if step["visual_references"] else ""
        print(f"  {step['step_id']} | {step['check_type']:8}{dur}{figs}")
        print(f"      section: {step['section']}")
        print(f"      {desc}{'…' if len(step['description']) > 70 else ''}")

    # Quality checks
    print("\n" + "=" * 60)
    print("QUALITY CHECK")
    print("=" * 60)
    steps = steps_json["steps"]
    no_section = sum(1 for s in steps if not s["section"])
    duration_steps = sum(1 for s in steps if s["check_type"] == "duration")
    with_figures = sum(1 for s in steps if s["visual_references"])
    print(f"  Steps without section : {no_section}/{len(steps)}")
    print(f"  Duration-check steps  : {duration_steps}")
    print(f"  Steps with figure refs: {with_figures}")
    if steps_json["total_steps"] == 0:
        print("\n⚠️  0 steps extracted — page range may only cover the title/TOC pages.")

    if args.out:
        Path(args.out).write_text(json.dumps(steps_json, indent=2), encoding="utf-8")
        print(f"\nSteps JSON saved to {args.out}")


if __name__ == "__main__":
    main()
