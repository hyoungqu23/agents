import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ValidationEnvironmentTests(unittest.TestCase):
    def run_validation(self, scenario):
        with tempfile.TemporaryDirectory(prefix="hm2-validator-test-") as directory:
            root = Path(directory)
            scripts = root / "repo/scripts"
            scripts.mkdir(parents=True)
            shutil.copy2(Path(__file__).parents[1] / "validate.sh", scripts / "validate.sh")
            for name in [".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"]:
                path = root / "repo" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")
            for plugin in ["one", "two"]:
                for platform in [".claude-plugin", ".codex-plugin"]:
                    path = root / "repo/plugins" / plugin / platform / "plugin.json"
                    path.parent.mkdir(parents=True)
                    path.write_text("{}")
            cache_root = root / "tmp"
            old_cache = cache_root / "hm2-agents-uv-cache"
            old_cache.mkdir(parents=True)
            (old_cache / "preserve.txt").write_text("original cache")
            validator = root / "validator.py"
            validator.write_text("# test validator")
            commands = root / "bin"
            commands.mkdir()
            # Command doubles isolate environment selection from installed Python,
            # uv, authentication and network state. The real shell script is executed.
            double = '''import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
scenario = os.environ["HM2_TEST_SCENARIO"]
cache = os.environ.get("UV_CACHE_DIR", "")
with open(os.environ["HM2_TEST_LOG"], "a") as log:
    log.write(json.dumps({"name": name, "args": args, "cache": cache}) + "\\n")
if name == "python3":
    if args == ["-c", "import yaml"]:
        sys.exit(0 if scenario == "system" else 1)
    if args[:2] == ["-m", "json.tool"]:
        json.load(open(args[2]))
elif name == "uv":
    probe = args[-2:] == ["-c", "import yaml"]
    if probe and (scenario == "unavailable" or
                  (scenario == "stale" and cache.endswith("hm2-agents-uv-cache"))):
        sys.exit(1)
    if not probe and scenario == "validator-fails":
        sys.exit(1)
'''
            for name in ["python3", "uv", "claude"]:
                executable = commands / name
                executable.write_text(f"#!{sys.executable}\n" + double)
                executable.chmod(0o755)
            log = root / "commands.jsonl"
            result = subprocess.run(
                ["bash", str(scripts / "validate.sh")],
                env={**os.environ, "PATH": f"{commands}{os.pathsep}{os.defpath}",
                     "TMPDIR": str(cache_root), "CODEX_PLUGIN_VALIDATOR": str(validator),
                     "HM2_TEST_SCENARIO": scenario, "HM2_TEST_LOG": str(log)},
                text=True, capture_output=True, timeout=15,
            )
            events = [json.loads(line) for line in log.read_text().splitlines()]
            fresh = {e["cache"] for e in events if e["cache"] and e["cache"] != str(old_cache)}
            self.assertEqual((old_cache / "preserve.txt").read_text(), "original cache")
            for path in fresh:
                self.assertFalse(Path(path).exists(), "owned temporary cache was not removed")
            return result, events, fresh

    def test_system_python_does_not_use_uv(self):
        result, events, fresh = self.run_validation("system")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(e["name"] == "uv" for e in events))
        self.assertFalse(fresh)

    def test_healthy_cache_is_reused_for_both_plugins(self):
        result, events, fresh = self.run_validation("healthy")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [e for e in events if e["name"] == "uv"]
        self.assertEqual(len(calls), 3)  # import probe and two validators
        self.assertEqual(len({e["cache"] for e in calls}), 1)
        self.assertFalse(fresh)

    def test_stale_cache_retries_once_in_owned_cache(self):
        result, events, fresh = self.run_validation("stale")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [e for e in events if e["name"] == "uv"]
        self.assertEqual(len(calls), 4)  # failed probe, fresh probe, two validators
        self.assertEqual(len(fresh), 1)
        self.assertEqual({e["cache"] for e in calls[1:]}, fresh)

    def test_failed_fresh_probe_stops_before_validators(self):
        result, events, fresh = self.run_validation("unavailable")
        self.assertNotEqual(result.returncode, 0)
        calls = [e for e in events if e["name"] == "uv"]
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(e["args"][-2:] == ["-c", "import yaml"] for e in calls))
        self.assertEqual(len(fresh), 1)
        self.assertFalse(any(e["name"] == "claude" for e in events))

    def test_real_validator_failure_is_not_hidden_or_retried(self):
        result, events, fresh = self.run_validation("validator-fails")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len([e for e in events if e["name"] == "uv"]), 2)
        self.assertFalse(fresh)
        self.assertFalse(any(e["name"] == "claude" for e in events))


if __name__ == "__main__":
    unittest.main()
