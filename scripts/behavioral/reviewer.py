"""A one-shot, file-based review capability for the isolated chain evaluator.

The coordinator requests review; the host runs a fixed Codex command in a protected
reviewer workspace, then publishes its reports to the author workspace. No arbitrary
shell command, model override or external path is accepted.
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
    def __init__(self, command, workspace, evidence, deadline, model, skill_snapshot=None):
        self.command = list(command)
        self.workspace = Path(workspace)
        self.evidence = Path(evidence)
        self.review_workspace = self.evidence / "reviewer-workspace"
        self.skill_snapshot = skill_snapshot or {}
        self.result = None
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
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        self.thread.join(timeout=5)

    def read_file(self, name, root=None):
        path = (root or self.workspace) / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required regular file missing: {name}")
        return path.read_bytes()

    def input_hashes(self, root=None):
        return {name: hashlib.sha256(self.read_file(name, root)).hexdigest()
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
                    # The author cannot write into this sibling sandbox. Sources are
                    # the runner's initial skill snapshot, not author-provided commands.
                    self.review_workspace.mkdir()
                    for name, data in self.skill_snapshot.items():
                        target = self.review_workspace / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                    for name in ("problem.md", "prd.md", "chain-notes.md",
                                 "authored.sha256.json", "review-prompt.txt"):
                        (self.review_workspace / name).write_bytes(self.read_file(name))
                    if self.input_hashes(self.review_workspace) != before:
                        raise ValueError("inputs changed while preparing reviewer workspace")
                    # Keep authoritative launch evidence outside the executor workspace.
                    launch = {"command": self.command, "model": self.model,
                              "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                              "before_sha256": before, "scope": "one fixed reviewer invocation"}
                    (self.evidence / "reviewer-launch.json").write_text(json.dumps(launch, indent=2) + "\n")
                    for name in ("review-events.jsonl", "review-stderr.log", "review-result.json"):
                        if (self.workspace / name).is_symlink():
                            raise ValueError(f"review output must not be a symlink: {name}")
                    with (self.evidence / "reviewer-events.jsonl").open("w") as out, \
                            (self.evidence / "reviewer-stderr.log").open("w") as err:
                        with self.lock:
                            if self.cancel.is_set():
                                return
                            self.process = subprocess.Popen(self.command, cwd=self.review_workspace,
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
                    events = [json.loads(line) for line in (self.evidence / "reviewer-events.jsonl").read_text().splitlines() if line.strip()]
                    if not all(isinstance(e, dict) for e in events):
                        raise RuntimeError("separate reviewer emitted malformed events")
                    if self.process.returncode or not any(e.get("type") == "turn.completed" for e in events) or \
                            any(e.get("type") in ("turn.failed", "error") for e in events):
                        raise RuntimeError("separate reviewer did not complete successfully")
                    result["after_sha256"] = self.input_hashes(self.review_workspace)
                    if result["after_sha256"] != before:
                        raise RuntimeError("reviewer changed author/source inputs")
                    if self.input_hashes() != before:
                        raise RuntimeError("author changed inputs during review")
                    if any(self.read_file(name, self.review_workspace) != data
                           for name, data in self.skill_snapshot.items()):
                        raise RuntimeError("reviewer changed skill sources")
                    reports = {name: self.read_file(name, self.review_workspace)
                               for name in ("report.md", "report.json")}
                    result["report_sha256"] = {name: hashlib.sha256(data).hexdigest()
                                               for name, data in reports.items()}
                    for name, data in reports.items():
                        if (self.workspace / name).is_symlink():
                            raise ValueError(f"report output must not be a symlink: {name}")
                        (self.workspace / name).write_bytes(data)
                    result["status"] = "completed"
                except (OSError, ValueError, TypeError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
                    result["error"] = str(error)
                if not self.cancel.is_set():
                    # Protected host evidence is authoritative. Publish the notification
                    # last, so a waiting coordinator cannot finish before it is recorded.
                    self.result = result
                    (self.evidence / "reviewer-result.json").write_text(json.dumps(result, indent=2) + "\n")
                    for host_name, name in (("reviewer-events.jsonl", "review-events.jsonl"),
                                            ("reviewer-stderr.log", "review-stderr.log")):
                        source = self.evidence / host_name
                        destination = self.workspace / name
                        if source.exists() and not destination.is_symlink():
                            destination.write_bytes(source.read_bytes())
                    destination = self.workspace / "review-result.json"
                    if not destination.is_symlink():
                        destination.write_text(json.dumps(result, indent=2) + "\n")
                return
            self.cancel.wait(0.2)
