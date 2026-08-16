import os
import json
import subprocess
import tempfile
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm
from backend.services.project_scaffolder import ProjectScaffolder


class ExecutionAgent:
    def __init__(self):
        self.skill = load_skill("execution_agent")

    async def execute(self, test_file_name, url, test_names=None):
        if not test_file_name or not os.path.isfile(test_file_name):
            return {
                "status": "error",
                "message": f"Test file not found: {test_file_name}",
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "logs": "",
                "screenshots": [],
                "broken_selectors": [],
                "is_real_bug": False,
                "failure_summary": "",
            }

        try:
            npx_path = self._find_npx()
            if not npx_path:
                return {
                    "status": "error",
                    "message": "npx/Node.js not found. Install Node.js to run Playwright tests.",
                    "passed": 0, "failed": 0, "skipped": 0,
                    "logs": "Node.js runtime not available",
                    "screenshots": [], "broken_selectors": [],
                    "is_real_bug": False, "failure_summary": "Node.js not found",
                }

            file_dir = os.path.dirname(test_file_name)
            test_file = os.path.basename(test_file_name)

            # Find the Playwright project root (where playwright.config.ts and node_modules live)
            project_root = self._find_output_dir(file_dir)
            if project_root:
                ProjectScaffolder(project_root).ensure(user_consent=True)
                # Run from project root so playwright.config.ts and node_modules are found
                cwd = project_root
                # Make test file path relative to project root
                try:
                    test_arg = os.path.relpath(test_file_name, project_root)
                except ValueError:
                    test_arg = test_file
            else:
                # Fallback: run from the test file's directory
                cwd = file_dir
                test_arg = test_file

            env = os.environ.copy()
            if url:
                env["TEST_URL"] = url

            cmd = [npx_path, "playwright", "test", test_arg, "--reporter=json"]
            if test_names:
                from backend.utils.test_parser import build_grep_pattern
                pattern = build_grep_pattern(test_names)
                if pattern:
                    cmd.extend(["--grep", pattern])

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=120000,
                env=env,
            )

            stdout = result.stdout
            stderr = result.stderr
            logs = stdout + "\n" + stderr

            report = self._parse_report(stdout)

            return {
                "status": "success" if report["failed"] == 0 else "failure",
                "message": f"Passed: {report['passed']}, Failed: {report['failed']}, Skipped: {report['skipped']}",
                "passed": report["passed"],
                "failed": report["failed"],
                "skipped": report["skipped"],
                "logs": logs[:5000],
                "screenshots": [],
                "broken_selectors": self._find_broken_selectors(logs),
                "is_real_bug": self._detect_real_bug(logs),
                "failure_summary": self._summarize_failures(logs),
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error", "message": "Test execution timed out after 120s",
                "passed": 0, "failed": 0, "skipped": 0, "logs": "Timeout",
                "screenshots": [], "broken_selectors": [],
                "is_real_bug": False, "failure_summary": "Timeout",
            }
        except Exception as e:
            return {
                "status": "error", "message": str(e),
                "passed": 0, "failed": 0, "skipped": 0, "logs": str(e),
                "screenshots": [], "broken_selectors": [],
                "is_real_bug": False, "failure_summary": str(e),
            }

    def _find_output_dir(self, start_dir):
        d = start_dir
        for _ in range(10):
            # Check if @playwright/test is actually installed
            if os.path.isdir(os.path.join(d, "node_modules", "@playwright", "test")):
                return d
            # Check for playwright.config.ts (scaffolded project)
            if os.path.isfile(os.path.join(d, "playwright.config.ts")):
                return d
            # Check package.json for dependency declaration
            pkg = os.path.join(d, "package.json")
            if os.path.isfile(pkg):
                try:
                    with open(pkg, "r") as f:
                        data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "@playwright/test" in deps:
                        return d
                except Exception:
                    pass
            parent = os.path.dirname(d)
            if parent == d:
                return None
            d = parent
        return None

    def _find_npx(self):
        for cmd in ["npx", "npx.cmd"]:
            try:
                r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return cmd
            except Exception:
                continue
        for p in os.environ.get("PATH", "").split(os.pathsep):
            for cmd in ["npx", "npx.cmd"]:
                fp = os.path.join(p, cmd)
                if os.path.isfile(fp) or os.path.isfile(fp + ".exe"):
                    return fp
        return None

    def _parse_report(self, stdout):
        passed = failed = skipped = 0
        # First try to parse the full JSON report from Playwright's --reporter=json
        try:
            data = json.loads(stdout)
            if isinstance(data, dict):
                stats = {"passed": 0, "failed": 0, "skipped": 0}
                def walk_suite(s):
                    for spec in s.get("specs", []):
                        for test_result in spec.get("tests", []):
                            status = test_result.get("status", "")
                            if status in ("passed", "expected"):
                                stats["passed"] += 1
                            elif status in ("failed", "unexpected"):
                                stats["failed"] += 1
                            elif status in ("skipped", "pending"):
                                stats["skipped"] += 1
                    for child in s.get("suites", []):
                        walk_suite(child)
                for suite in data.get("suites", []):
                    walk_suite(suite)
                return stats
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

        # Fallback: try parsing Playwright's JSON-lines format (one JSON object per line)
        try:
            stats = {"passed": 0, "failed": 0, "skipped": 0}
            for line in stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        status = obj.get("status", "")
                        if status == "passed":
                            stats["passed"] += 1
                        elif status == "failed":
                            stats["failed"] += 1
                        elif status in ("skipped", "pending"):
                            stats["skipped"] += 1
                except json.JSONDecodeError:
                    continue
            if stats["passed"] > 0 or stats["failed"] > 0 or stats["skipped"] > 0:
                return stats
        except Exception:
            pass

        # Last resort: parse the human-readable summary line (e.g. "3 passed, 1 failed, 2 skipped")
        for line in stdout.split("\n"):
            lower = line.lower()
            if "passed" in lower and "failed" in lower:
                parts = line.split()
                for j, p in enumerate(parts):
                    pl = p.lower().strip(",. ")
                    if pl == "passed" and j > 0:
                        try:
                            passed = int(parts[j - 1])
                        except ValueError:
                            pass
                    elif pl == "failed" and j > 0:
                        try:
                            failed = int(parts[j - 1])
                        except ValueError:
                            pass
                    elif pl in ("skipped", "pending") and j > 0:
                        try:
                            skipped = int(parts[j - 1])
                        except ValueError:
                            pass
                break
        return {"passed": passed, "failed": failed, "skipped": skipped}

    def _find_broken_selectors(self, logs):
        broken = []
        import re
        patterns = [
            r"(?:locator|selector|element).*?(?:not found|not visible|not attached|not stable)",
            r"(?:TimeoutError|timeout).*?(?:locator|selector|waiting)",
            r"page\.(?:locator|click|fill|selectOption|check|uncheck).*?\(.*?\).*?(?:fail|error|timeout)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            for m in matches:
                broken.append({"pattern": m, "type": "selector_error"})
        return broken

    def _detect_real_bug(self, logs):
        bug_indicators = [
            "500", "Internal Server Error", "assertion failed",
            "expected", "to be", "received",
        ]
        count = sum(1 for ind in bug_indicators if ind.lower() in logs.lower())
        return count >= 2

    def _summarize_failures(self, logs):
        lines = logs.split("\n")
        failure_lines = []
        capture = False
        for line in lines:
            if "FAIL" in line or "failed" in line.lower():
                capture = True
            if capture:
                failure_lines.append(line)
                if len(failure_lines) > 20:
                    break
        return "\n".join(failure_lines)
