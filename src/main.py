from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "graph"))

import argparse
from datetime import datetime
from pathlib import Path
from graph import graph

def slugify(s: str) -> str:
    """Convert string to slug for filename."""
    return s.lower().replace(" ", "-").replace(",", "").replace(".", "")

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
    config = {"configurable": {"thread_id": "demo-1"}}
    
    print(f"\nStarting acquisition research for: {target}\n")
    result = graph.invoke({"target": target}, config)

    # Save report to reports/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    slug = slugify(f"{args.target}_{args.location}")
    report_path = Path(__file__).parent.parent / "reports" / f"{timestamp}_{slug}.md"
    report_path.parent.mkdir(exist_ok=True)
    
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
