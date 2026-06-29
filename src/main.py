from dotenv import load_dotenv
load_dotenv()

import argparse
from datetime import datetime
from pathlib import Path
# Imports use bare package names (graph, utils) because `python src/main.py`
# puts src/ on sys.path[0]. Tests import via src.graph.graph because pytest
# adds the repo root. Both resolve to the same files.
from graph.graph import graph
from utils import slugify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition Research Agent — Generate McKinsey-style pre-acquisition reports"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="Air conditioning repair services",
        help="Business category to research"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Los Angeles, CA",
        help="Geographic location"
    )
    args = parser.parse_args()

    target = f"{args.target} in {args.location}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    slug = slugify(f"{args.target}_{args.location}")
    thread_id = f"{slug}-{timestamp}"
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\nStarting acquisition research for: {target}\n")
    result = graph.invoke({"target": target}, config)

    # Save report to reports/
    report_path = Path(__file__).parent.parent / "reports" / f"{timestamp}_{slug}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_content = f"""# Acquisition Research Report: {args.target} in {args.location}

Generated: {datetime.now().isoformat()}

---

## Executive Summary

{result['evaluation']}

---

## Full Report

{result['report']}
"""
    
    report_path.write_text(report_content)
    
    print(f"✅ Report saved to: {report_path}")
    print(f"\n📄 Full report:\n{report_content}")
