import json
import uuid
import sys
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm, extract_json


class ManualTestAgent:
    def __init__(self):
        self.skill = load_skill("manual_test_agent")

    async def generate(self, context, mode="fresh", existing_cases=None):
        requirement = context.get("requirement", "") or context.get("requirement_preview", "")
        url = context.get("url", "") or context.get("resolved_url", "")

        system_prompt = self.skill
        existing_text = json.dumps(existing_cases, indent=2) if existing_cases else "None"

        user_prompt = f"""
Mode: {mode}
URL: {url}
Requirement: {requirement[:2000]}

Existing Test Cases:
{existing_text}

Generate a comprehensive set of manual test cases in {mode} mode.
For fresh mode include all of the following:
- 3-5 happy path tests
- 3-5 negative tests
- 2-3 edge case tests
- 1-2 smoke tests

Return ONLY valid JSON: {{"test_cases": [{{"id": "", "title": "", "feature": "", "priority": "", "test_type": "", "preconditions": "", "steps": "", "expected_result": "", "tags": [], "status": "active"}}]}}
"""
        try:
            content = await call_llm(system_prompt, user_prompt, max_tokens=8192)
            result = extract_json(content)
            if isinstance(result, dict):
                cases = result.get("test_cases") or []
            elif isinstance(result, list):
                cases = result
            else:
                cases = []
            cases = [self._normalize_case(c) for c in cases if isinstance(c, dict)]
            if cases:
                return cases
            print("[MANUAL TEST AGENT] LLM returned no usable test_cases, using fallback.", file=sys.stderr)
        except Exception as e:
            print(f"[MANUAL TEST AGENT] Generation failed ({e}), using fallback.", file=sys.stderr)
        return self._fallback(requirement)

    def _normalize_case(self, c):
        steps = c.get("steps")
        if isinstance(steps, list):
            steps = "\n".join(str(s).strip() for s in steps if str(s).strip())
        steps = str(steps or "").strip()

        preconditions = c.get("preconditions")
        if isinstance(preconditions, list):
            preconditions = "\n".join(str(p).strip() for p in preconditions if str(p).strip())
        preconditions = str(preconditions or "").strip()

        tags = c.get("tags")
        if not isinstance(tags, list):
            tags = [t for t in str(tags or "").split(",") if t.strip()]

        cid = c.get("id") or str(uuid.uuid4())
        if not isinstance(cid, str):
            cid = str(cid)

        return {
            "id": cid,
            "title": str(c.get("title") or "").strip() or f"Test - {c.get('feature') or 'General'}",
            "feature": str(c.get("feature") or "General").strip(),
            "priority": str(c.get("priority") or "medium").strip() or "medium",
            "test_type": str(c.get("test_type") or "happy path").strip() or "happy path",
            "preconditions": preconditions,
            "steps": steps,
            "expected_result": str(c.get("expected_result") or "").strip(),
            "tags": tags,
            "status": "active",
        }

    def _fallback(self, requirement):
        cases = []
        for i, test_type in enumerate(["happy path", "negative", "edge case", "smoke"]):
            cases.append({
                "id": str(uuid.uuid4()),
                "title": f"{test_type.title()} - {requirement[:50] if requirement else 'Basic'}",
                "feature": "General",
                "priority": "medium",
                "test_type": test_type,
                "preconditions": "Application is accessible",
                "steps": "1. Navigate to the application\n2. Perform the action\n3. Verify the result",
                "expected_result": "The operation completes as expected",
                "tags": ["@manual", f"@{test_type.replace(' ', '-')}"],
                "status": "active",
            })
        return cases
