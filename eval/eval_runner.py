"""
Usage:
    python eval/eval_runner.py                     # run all cases
    python eval/eval_runner.py --category safety   # filter by category
    python eval/eval_runner.py --model qwen/qwen3-32b  # use specific model
    python eval/eval_runner.py --report eval/report.json  # save detailed JSON
"""

import argparse
import glob
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

BACKEND_URL = "http://localhost:8000"
EVAL_DIR = Path(__file__).parent
CASES_FILE = EVAL_DIR / "eval_cases.json"
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"

# Helpers

def normalize_sql(sql: str) -> str:
    """Lowercase, collapse whitespace, strip trailing semicolons."""
    s = sql.lower().strip().rstrip(";")
    s = re.sub(r"\s+", " ", s)
    return s


def sql_matches_pattern(sql: str, pattern: str) -> bool:
    """Check whether the generated SQL matches a loose regex pattern."""
    return bool(re.search(pattern, normalize_sql(sql), re.IGNORECASE))


def result_approx_match(agent_value: Any, expected: float, tolerance: float) -> bool:
    """Check whether a numeric result is within tolerance of expected."""
    try:
        val = float(str(agent_value).replace(",", ""))
        return abs(val - expected) / max(abs(expected), 1) <= tolerance
    except (ValueError, TypeError):
        return False


def result_contains(agent_value: Any, expected_str: str) -> bool:
    """Check whether the result string contains expected substring."""
    return expected_str.lower() in str(agent_value).lower()


# Log parsing — read JSONL logs to get tool calls and SQL

def get_latest_log_file() -> Path | None:
    """Find the most recent JSONL log file."""
    log_files = sorted(glob.glob(str(LOGS_DIR / "chat_*.jsonl")))
    return Path(log_files[-1]) if log_files else None


def parse_logs_for_question(question: str) -> dict:
    """Parse JSONL logs to find tool calls and SQL for a specific question.

    Returns dict with keys: tool_calls, sql, snapshot_id, result
    """
    info = {"tool_calls": [], "sql": None, "snapshot_id": None, "result": None}

    log_file = get_latest_log_file()
    if not log_file:
        return info

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            event = entry.get("event", "")

            # Match tool_call events that contain our question's SQL
            if event == "tool_call":
                tool_name = entry.get("tool", "")
                args = entry.get("arguments", {})
                sql = args.get("sql", "")
                if sql:
                    info["tool_calls"].append(tool_name)
                    info["sql"] = sql
                    if "snapshot_id" in args:
                        info["snapshot_id"] = args["snapshot_id"]

            elif event == "tool_result":
                result = entry.get("result", {})
                if isinstance(result, dict):
                    info["result"] = result

    return info


# Chat call

def call_chat(question: str, model: str = "qwen/qwen3-32b", session_id: str = "eval") -> dict:
    """Send a single question to the /chat endpoint, return parsed response."""
    payload = {
        "messages": [{"role": "user", "content": question}],
        "model": model,
        "session_id": session_id,
        "user_role": "analyst",
    }
    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()



# Evaluation logic


def evaluate_case(case: dict, model: str) -> dict:
    """Run one test case and return a result dict."""
    result = {
        "id": case["id"],
        "question": case["question"],
        "category": case.get("category", "uncategorized"),
        "passed": False,
        "checks": {},
        "error": None,
        "latency_ms": None,
        "actual_tool": None,
        "actual_sql": None,
    }

    start = time.time()
    try:
        response = call_chat(case["question"], model=model, session_id=f"eval_{case['id']}")
        result["latency_ms"] = int((time.time() - start) * 1000)
        answer = response.get("content", "")
    except Exception as e:
        result["error"] = str(e)
        result["latency_ms"] = int((time.time() - start) * 1000)
        return result

    # Parse logs to get actual tool call and SQL
    time.sleep(0.5)  # small delay to ensure log is written
    log_info = parse_logs_for_question(case["question"])
    result["actual_tool"] = log_info["tool_calls"][-1] if log_info["tool_calls"] else None
    result["actual_sql"] = log_info["sql"]

    # Check: expected tool
    if "expected_tool" in case:
        expected_tool = case["expected_tool"]
        if expected_tool == "none":
            # For safety cases, agent should NOT call any tool
            result["checks"]["tool_not_called"] = result["actual_tool"] is None
        else:
            # Check if the expected tool was called
            result["checks"]["tool_used"] = result["actual_tool"] == expected_tool

    # Check: response contains keyword
    if "expected_response_contains" in case:
        keywords = case["expected_response_contains"].split("|")
        result["checks"]["response_contains"] = any(kw.lower() in answer.lower() for kw in keywords)

    # Check: result contains value
    if "expected_result_contains" in case:
        result["checks"]["result_contains"] = result_contains(answer, case["expected_result_contains"])

    # Check: SQL pattern match
    if "expected_sql_pattern" in case and result["actual_sql"]:
        result["checks"]["sql_pattern"] = sql_matches_pattern(result["actual_sql"], case["expected_sql_pattern"])
    elif "expected_sql_pattern" in case and not result["actual_sql"]:
        result["checks"]["sql_pattern"] = False  # no SQL was generated

    # Check: approximate numeric result
    if "expected_result_approx" in case:
        # Try to extract a number from the answer
        numbers = re.findall(r"[\$]?([\d,]+\.?\d*)", answer.replace(",", ""))
        if numbers:
            matched = False
            for num_str in numbers:
                try:
                    num = float(num_str.replace(",", ""))
                    if result_approx_match(num, case["expected_result_approx"], case.get("tolerance", 0.01)):
                        result["checks"]["result_approx"] = True
                        matched = True
                        break
                except ValueError:
                    continue
            if not matched:
                result["checks"]["result_approx"] = False
        else:
            result["checks"]["result_approx"] = False

    result["passed"] = all(result["checks"].values()) if result["checks"] else False
    return result



# Report


def print_report(results: list[dict], elapsed_sec: float):
    """Print a human-readable summary."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    errors = sum(1 for r in results if r["error"])

    print("\n" + "=" * 70)
    print("  EVALUATION REPORT")
    print("=" * 70)
    print(f"  Total cases : {total}")
    if total:
        print(f"  Passed      : {passed}  ({passed/total*100:.0f}%)")
    print(f"  Failed      : {failed}")
    print(f"  Errors      : {errors}")
    print(f"  Time        : {elapsed_sec:.1f}s")
    print("-" * 70)

    # By category
    categories = {}
    for r in results:
        cat = r["category"]
        categories.setdefault(cat, {"passed": 0, "total": 0})
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    print("  By Category:")
    for cat, stats in sorted(categories.items()):
        pct = stats["passed"] / stats["total"] * 100 if stats["total"] else 0
        status = "PASS" if stats["passed"] == stats["total"] else "FAIL"
        print(f"    {cat:20s}  {stats['passed']}/{stats['total']}  ({pct:.0f}%)  [{status}]")

    print("-" * 70)
    print("  Failed Cases:")
    for r in results:
        if not r["passed"]:
            err = f"  ERROR: {r['error']}" if r["error"] else ""
            print(f"    [{r['id']}] {r['question'][:60]}{err}")
            if r["actual_tool"]:
                print(f"           Tool called: {r['actual_tool']}")
            if r["actual_sql"]:
                print(f"           SQL: {r['actual_sql'][:80]}...")
            if r["checks"]:
                for check, val in r["checks"].items():
                    if not val:
                        print(f"           FAIL: {check}")
    print("=" * 70 + "\n")


def save_report(results: list[dict], path: Path):
    """Save detailed JSON report."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": f"{passed/total*100:.0f}%" if total else "0%",
        "results": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Detailed report saved to {path}")



# Main


def main():
    parser = argparse.ArgumentParser(description="Evaluate retail lakehouse agent")
    parser.add_argument("--model", default="qwen/qwen3-32b", help="Model to test")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--report", help="Path to save JSON report")
    parser.add_argument("--cases", default=str(CASES_FILE), help="Path to eval_cases.json")
    args = parser.parse_args()

    with open(args.cases) as f:
        cases = json.load(f)

    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]

    if not cases:
        print("No test cases to run.")
        sys.exit(0)

    print(f"Running {len(cases)} test cases with model={args.model}...")
    start = time.time()
    results = [evaluate_case(c, args.model) for c in cases]
    elapsed = time.time() - start

    print_report(results, elapsed)

    report_path = Path(args.report) if args.report else EVAL_DIR / "report.json"
    save_report(results, report_path)


if __name__ == "__main__":
    main()
