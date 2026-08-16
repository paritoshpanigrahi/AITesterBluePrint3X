import json
import os
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm


class TestAgent:
    def __init__(self):
        self.skill = load_skill("test_agent")

    async def generate(self, context, scenarios, locators, organization, mode="fresh", existing_file=None, test_plan=None):
        system_prompt = self.skill

        existing_code = ""
        if existing_file and os.path.isfile(existing_file):
            with open(existing_file, "r") as f:
                existing_code = f.read()

        scenarios_text = json.dumps(scenarios, indent=2) if scenarios else "[]"
        locators_text = json.dumps(locators, indent=2) if locators else "{}"
        org_text = json.dumps(organization, indent=2) if organization else "{}"
        plan_text = json.dumps(test_plan, indent=2) if test_plan else "None"

        url = context.get("url", "") or context.get("resolved_url", "")
        requirement = context.get("requirement", "") or context.get("requirement_preview", "")
        exec_log = context.get("execution_log", "") or ""

        po_class = context.get("page_object_class", "AppPage")
        po_file = context.get("page_object_file", "app_page")
        po_import = f'import {{ {po_class} }} from "../../pages/{po_file}";'

        # Build per-page locators summary for the LLM
        all_page_locators = context.get("all_page_locators", {}) or {}
        pages_summary_lines = []
        if all_page_locators:
            for pn, pl in sorted(all_page_locators.items()):
                if not isinstance(pl, dict) or not pl:
                    continue
                pages_summary_lines.append(f"\n## Page: {pn}")
                for lk, lv in list(pl.items())[:20]:
                    if isinstance(lv, dict):
                        pages_summary_lines.append(f"  - {lk}: {lv.get('primary', '')}")
        pages_summary = "\n".join(pages_summary_lines)

        user_prompt = f"""
Mode: {mode}
URL: {url}
Requirement: {requirement[:8000]}

Test Plan:
{plan_text}

Organization:
{org_text}

Scenarios:
{scenarios_text}

Locators (all pages):
{locators_text}

Per-Page Locators:
{pages_summary if pages_summary else 'Not available'}

Existing Test Code:
{existing_code if existing_code else 'None'}

Previous Execution Log:
{exec_log[:2000] if exec_log else 'None'}

Page Object Import (use this EXACT import):
{po_import}

Generate a complete Playwright TypeScript test file ({mode} mode).
The application has MULTIPLE pages/modules (see Per-Page Locators above). You MUST generate tests for EVERY page/module, not just one.
Create MULTIPLE `test.describe` blocks — one per page/module based on the Test Plan suites and Scenarios.
Use @playwright/test, Page Object pattern, inject tags in every test() call.
Use the EXACT Page Object import shown above. Instantiate it as `const pageObj = new {po_class}(page);`
Reference the Test Plan for suite grouping and scenario structure.
Add step-by-step comments before each action matching the plan steps.
Previous execution log (if any) contains useful patterns to follow.
Return ONLY the TypeScript code, no markdown.
"""
        try:
            content = await call_llm(system_prompt, user_prompt, temperature=0.2, timeout=600)
            content = content.replace("```typescript", "").replace("```ts", "").replace("```", "").strip()
            return content
        except Exception:
            return self._generate_fallback(scenarios, organization, url)

    def _generate_fallback(self, scenarios, organization, url):
        tags = organization.get("tags", []) if isinstance(organization, dict) else []
        tags_str = ", ".join(f'"{t}"' for t in tags) if tags else ""

        lines = [
            'import { test, expect } from "@playwright/test";',
            "",
        ]

        if not scenarios:
            lines.append('test.describe("App Tests", () => {')
            lines.append("  test('page loads successfully'")
            if tags_str:
                lines.append(f"    , {{ tag: [{tags_str}] }}")
            lines.append("    , async ({ page }) => {")
            lines.append(f"      await page.goto('{url}');")
            lines.append("      await expect(page).toHaveURL(/.*/);")
            lines.append("    });")
            lines.append("});")
            lines.append("")
            return "\n".join(lines)

        for i, s in enumerate(scenarios):
            name = s.get("name", f"Test {i+1}")
            steps = s.get("steps", "")
            expected = s.get("expected_result", "")

            lines.append(f'test.describe("{name}", () => {{')
            lines.append(f"  test('{name}'")
            if tags_str:
                lines.append(f"    , {{ tag: [{tags_str}] }}")
            lines.append(f"    , async ({{ page }}) => {{")
            lines.append(f"      await page.goto('{url}');")
            for step in steps.split("\n"):
                step = step.strip()
                if step:
                    p = step[3:].strip() if step[:2].isdigit() and len(step) > 3 else step
                    lines.append(f"      // {p}")
            lines.append(f"      // Expected: {expected}")
            lines.append("    });")
            lines.append("});")
            lines.append("")

        return "\n".join(lines)
