import re
import os


def parse_test_file(filepath):
    if not filepath or not os.path.isfile(filepath):
        err_msg = f"File not found: {filepath}"
        import sys; print(f"[TEST PARSER] {err_msg}", file=sys.stderr)
        return {"file": filepath or "", "suites": [], "error": err_msg}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    suites = []
    current_suite = None
    suite_start = 0

    lines = content.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()

        describe_match = re.match(r"test\.describe\s*\(\s*['\"]([^'\"]+)['\"]", stripped)
        if describe_match:
            if current_suite is not None:
                current_suite["tests"] = _extract_tests(
                    "\n".join(lines[suite_start:i])
                )
            current_suite = {
                "name": describe_match.group(1),
                "line": i + 1,
                "tests": [],
            }
            suites.append(current_suite)
            suite_start = i
            continue

        test_match = re.match(
            r"test\s*\(\s*['\"]([^'\"]+)['\"]", stripped
        )
        if test_match:
            is_nested = False
            for j in range(max(0, i - 5), i):
                if "test.describe" in lines[j]:
                    is_nested = True
                    break
            if current_suite and not is_nested:
                current_suite.setdefault("tests", []).append(
                    {"name": test_match.group(1), "line": i + 1}
                )

    if current_suite is not None:
        current_suite["tests"] = _extract_tests(
            "\n".join(lines[suite_start:])
        )

    total_tests = sum(len(s.get("tests", [])) for s in suites)
    import sys; print(f"[TEST PARSER] Parsed {filepath}: {len(suites)} suites, {total_tests} tests", file=sys.stderr)
    return {"file": filepath, "suites": suites}


def _extract_tests(section):
    tests = []
    for m in re.finditer(
        r"(?:^|\n)\s*test\s*\(\s*['\"]([^'\"]+)['\"]", section
    ):
        name = m.group(1)
        if name not in [t["name"] for t in tests]:
            tests.append({"name": name, "line": section[: m.start()].count("\n") + 1})
    return tests


def build_grep_pattern(test_names):
    if not test_names:
        return None
    escaped = [re.escape(n) for n in test_names]
    return "(" + "|".join(escaped) + ")"
