"""A one-shot, file-based review capability for the isolated chain evaluator.

The coordinator requests review; the host runs a fixed Codex command in the same
workspace. No arbitrary shell command, model override or external path is accepted.
This avoids nesting a CLI app-server inside the author's OS sandbox.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time


class ReviewerBridge:
    def __init__(self, command, workspace, evidence, deadline, model):
        self.command = list(command)
        self.workspace = Path(workspace)
        self.evidence = Path(evidence)
        self.deadline = deadline
        self.model = model
        self.cancel = threading.Event()
        self.lock = threading.Lock()
        self.process = None
        self.thread = threading.Thread(target=self.serve, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        with self.lock:
            self.cancel.set()
            if self.process is not None and self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGKILL)
        self.thread.join(timeout=5)

    def read_file(self, name):
        path = self.workspace / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required regular file missing: {name}")
        return path.read_bytes()

    def input_hashes(self):
        return {name: hashlib.sha256(self.read_file(name)).hexdigest()
                for name in ("problem.md", "prd.md", "chain-notes.md")}

    def serve(self):
        request = self.workspace / "review-request.json"
        while not self.cancel.is_set() and time.monotonic() < self.deadline:
            if request.exists() or request.is_symlink():
                result = {"status": "failed", "executor": "host ReviewerBridge"}
                try:
                    data = json.loads(self.read_file("review-request.json"))
                    if data != {"action": "review", "prompt_path": "review-prompt.txt"}:
                        raise ValueError("unsupported request; only fixed review capability is allowed")
                    prompt = self.read_file("review-prompt.txt").decode("utf-8")
                    if len(prompt) > 65536:
                        raise ValueError("review prompt exceeds 64 KiB")
                    before = self.input_hashes()
                    authored = json.loads(self.read_file("authored.sha256.json"))
                    if authored != {name: before[name] for name in ("problem.md", "prd.md")}:
                        raise ValueError("authored hashes do not match inputs before review")
                    result["before_sha256"] = before
                    # Keep authoritative launch evidence outside the executor workspace.
                    launch = {"command": self.command, "model": self.model,
                              "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                              "before_sha256": before, "scope": "one fixed reviewer invocation"}
                    (self.evidence / "reviewer-launch.json").write_text(json.dumps(launch, indent=2) + "\n")
                    for name in ("review-events.jsonl", "review-stderr.log", "review-result.json"):
                        if (self.workspace / name).is_symlink():
                            raise ValueError(f"review output must not be a symlink: {name}")
                    with (self.workspace / "review-events.jsonl").open("w") as out, \
                            (self.workspace / "review-stderr.log").open("w") as err:
                        with self.lock:
                            if self.cancel.is_set():
                                return
                            self.process = subprocess.Popen(self.command, cwd=self.workspace,
                                stdin=subprocess.PIPE, stdout=out, stderr=err, text=True,
                                start_new_session=True,
                                env={**os.environ, "PRODUCT_EVAL_MODEL": self.model})
                        try:
                            self.process.communicate(prompt, timeout=max(0.1, self.deadline-time.monotonic()))
                        except subprocess.TimeoutExpired:
                            if self.process.poll() is None:
                                os.killpg(self.process.pid, signal.SIGKILL)
                            self.process.communicate()
                            raise TimeoutError("separate reviewer exceeded chain deadline")
                    result["returncode"] = self.process.returncode
                    events = [json.loads(line) for line in self.read_file("review-events.jsonl").decode().splitlines() if line.strip()]
                    if self.process.returncode or not any(e.get("type") == "turn.completed" for e in events) or \
                            any(e.get("type") in ("turn.failed", "error") for e in events):
                        raise RuntimeError("separate reviewer did not complete successfully")
                    result["after_sha256"] = self.input_hashes()
                    if result["after_sha256"] != before:
                        raise RuntimeError("reviewer changed author/source inputs")
                    result["status"] = "completed"
                except (OSError, ValueError, TypeError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
                    result["error"] = str(error)
                if not self.cancel.is_set():
                    # Result metadata contains no authoring/review judgment.
                    destination = self.workspace / "review-result.json"
                    if not destination.is_symlink():
                        destination.write_text(json.dumps(result, indent=2) + "\n")
                    (self.evidence / "reviewer-result.json").write_text(json.dumps(result, indent=2) + "\n")
                return
            self.cancel.wait(0.2)
