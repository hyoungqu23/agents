#!/usr/bin/env python3
"""Run real Codex skill invocations in disposable workspaces; keep evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from cases import CASES, prepare, snapshot, grade

REPO = Path(__file__).resolve().parents[2]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def execute(command, prompt, cwd, directory, timeout):
    with (directory / "events.jsonl").open("w") as out, (directory / "stderr.log").open("w") as err:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=out,
                                   stderr=err, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill the process group, including unfinished tool subprocesses.
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise TimeoutError(f"executor exceeded {timeout}s")
    if process.returncode:
        raise RuntimeError(f"executor exited {process.returncode}; see stderr.log")
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines() if line.strip()]
    if not all(isinstance(e, dict) for e in events):
        raise RuntimeError("executor emitted malformed events")
    if not any(e.get("type") == "turn.completed" for e in events) or any(e.get("type") in ("turn.failed", "error") for e in events):
        raise RuntimeError("executor did not complete a successful turn")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Explicit model ID, recorded in evidence")
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the repository")
    parser.add_argument("--case", choices=CASES, action="append", dest="cases")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per scenario")
    args = parser.parse_args()
    output = args.output.resolve()
    if output == REPO or REPO in output.parents:
        parser.error("use an output directory outside the repository")
    if args.timeout < 1:
        parser.error("timeout must be positive")
    output.mkdir(parents=True, exist_ok=False)
    selected = list(dict.fromkeys(args.cases or CASES))
    summary = {"started_at": datetime.now(timezone.utc).isoformat(), "model": args.model,
               "reasoning_effort": "low", "scope": "behavioral smoke, not full qualitative evaluation",
               "full_suite": set(selected) == set(CASES),
               "not_run": [case for case in CASES if case not in selected],
               "cases": [], "status": "error"}
    # Persist even if Codex is missing or another preflight fails.
    write_json(output / "summary.json", summary)
    try:
        summary["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        summary["working_tree"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True)
        summary["codex_version"] = subprocess.check_output(["codex", "--version"], text=True).strip()
        summary["harness_sha256"] = hashes({p.name: p.read_bytes() for p in Path(__file__).parent.glob("*.py")})
        for case in selected:
            directory = output / case
            workspace = directory / "workspace"
            workspace.mkdir(parents=True)
            result = {"case": case, "status": "error", "checks": []}
            summary["cases"].append(result)
            start = time.monotonic()
            try:
                prompt, before, origin = prepare(REPO, case, workspace)
                result["scenario"] = origin
                (directory / "prompt.txt").write_text(prompt)
                for name, content in before.items():
                    original = directory / "before" / name
                    original.parent.mkdir(parents=True, exist_ok=True)
                    original.write_bytes(content)
                write_json(directory / "before.sha256.json", hashes(before))
                command = ["codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                           "--sandbox", "workspace-write", "--model", args.model,
                           "-c", 'model_reasoning_effort="low"', "-c", 'web_search="disabled"',
                           "--json", "--color", "never", "-"]
                result["command"] = command
                execute(command, prompt, workspace, directory, args.timeout)
                after = snapshot(workspace)
                write_json(directory / "after.sha256.json", hashes(after))
                result["checks"] = grade(case, before, after)
                result["status"] = "passed" if all(c["passed"] for c in result["checks"]) else "failed"
            except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
                result["error"] = str(error)
            result["duration_seconds"] = round(time.monotonic() - start, 2)
            write_json(directory / "result.json", result)
            write_json(output / "summary.json", summary)
            print(f"{case}: {result['status']}", flush=True)
        summary["status"] = "passed" if all(r["status"] == "passed" for r in summary["cases"]) else "failed"
    except (OSError, subprocess.SubprocessError) as error:
        summary["error"] = str(error)
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "summary.json", summary)
    print(f"Evidence: {output}", flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
