import os
import json
import uuid
from datetime import datetime

from backend.agents.locator_agent import LocatorAgent
from backend.agents.requirement_agent import RequirementAgent
from backend.agents.organization_agent import OrganizationAgent
from backend.agents.test_agent import TestAgent
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.healing_agent import HealingAgent
from backend.agents.planner_agent import PlannerAgent
from backend.ingestion.context_builder import ContextBuilder
from backend.services.duplicate_detector import DuplicateDetector
from backend.services.test_generator import TestGenerator
from backend.services.test_registry import TestRegistry
from backend.services.crawler import Crawler
from backend.services.project_scaffolder import ProjectScaffolder
from backend.utils.file_writer import FileWriter
from backend.utils.test_parser import parse_test_file
from backend.agents._client_factory import configure as configure_llm, get_and_clear_llm_errors


class Orchestrator:
    def __init__(self):
        self.locator_agent = LocatorAgent()
        self.requirement_agent = RequirementAgent()
        self.organization_agent = OrganizationAgent()
        self.test_agent = TestAgent()
        self.execution_agent = ExecutionAgent()
        self.healing_agent = HealingAgent()
        self.planner_agent = PlannerAgent()
        self.context_builder = ContextBuilder("")
        self.duplicate_detector = DuplicateDetector("")
        self.test_generator = TestGenerator()
        self.crawler = Crawler()

    async def run(self, req, mode="fresh", feature_name=None, test_file_name=None, output_dir=None):
        if not output_dir:
            output_dir = os.getenv("OUTPUT_DIR", "")

        llm_provider = getattr(req, "llm_provider", None) or None
        llm_api_key = getattr(req, "llm_api_key", None) or None
        llm_model = getattr(req, "llm_model", None) or None
        llm_max_tokens = getattr(req, "llm_max_tokens", 0) or 0
        if llm_provider or llm_api_key or llm_model or llm_max_tokens:
            configure_llm(provider=llm_provider, api_key=llm_api_key, model=llm_model, max_tokens=llm_max_tokens)
        get_and_clear_llm_errors()
        self.context_builder = ContextBuilder(output_dir)
        self.duplicate_detector = DuplicateDetector(output_dir)
        registry = TestRegistry(output_dir)
        file_writer = FileWriter(output_dir)

        scaffolder = ProjectScaffolder(output_dir)
        setup_check = scaffolder.check()
        user_setup_consent = getattr(req, "setup_playwright", None) or False
        if not setup_check.get("playwright_installed"):
            if not user_setup_consent:
                return {
                    "status": "setup_required",
                    "message": "Playwright is not set up at the output directory. Set setup_playwright=true to scaffold it, or use the /setup-playwright endpoint.",
                    "setup_playwright_required": True,
                    "setup_check": setup_check,
                    "locators": {},
                    "scenarios": [],
                    "test_file_path": "",
                    "execution_result": None,
                    "healing_result": None,
                    "registry_entries": [],
                    "report_path": "",
                    "duplicate_result": None,
                    "organization": None,
                    "test_plan": None,
                    "test_structure": None,
                    "auto_run_available": False,
                    "project_scaffold": setup_check,
                }
            scaffold_result = scaffolder.ensure(user_consent=True)
        else:
            scaffold_result = {"scaffolded": False, "message": "Playwright project already exists"}

        context = await self.context_builder.build(req)
        url = req.url or context.get("resolved_url", "")
        codebase_path = getattr(req, "codebase_path", None)

        locators, page_locators = await self.locator_agent.generate(url, codebase_path, context.get("codebase_context", {}))
        context["locators"] = locators
        context["page_locators"] = page_locators

        test_plan = await self.planner_agent.create_plan(context, mode)
        context["test_plan"] = test_plan

        if req.steps:
            context["input_type"] = "steps"
            context["requirement"] = "\n".join(req.steps)
        else:
            context["input_type"] = "requirement"

        scenarios = await self.requirement_agent.parse(context, mode)

        # Coverage amplification: ask LLM to identify and fill gaps
        if scenarios:
            from backend.agents._client_factory import call_llm, extract_json
            try:
                existing_summary = "\n".join(f"- {s.get('name', '')}" for s in scenarios[:30])
                amp_prompt = f"""You are a test coverage analyst. Review these existing test scenarios for the web application with pages: {', '.join(r for r in context.get('codebase_context', {}).get('routes', [])[:15]) if context.get('codebase_context') else context.get('resolved_url', '')}.

Existing scenarios:
{existing_summary}

What IMPORTANT test scenarios are MISSING? Focus on:
1. Role-based access control (admin vs regular user)
2. Empty states and edge cases
3. Input validation and error handling
4. Cross-feature workflows (login → browse → create → logout)
5. CRUD lifecycle tests (create → verify → edit → verify → delete)
6. Negative tests (invalid data, unauthorized actions)

Return ONLY a JSON array: [{{"name": "...", "steps": "1. ...\\n2. ...", "expected_result": "..."}}]
Return an empty array [] if coverage is already comprehensive.
"""
                amp_result = await call_llm("You are a test coverage analyst.", amp_prompt, temperature=0.4, timeout=300)
                amp_scenarios = extract_json(amp_result)
                if isinstance(amp_scenarios, list) and len(amp_scenarios) > 0:
                    existing_names = {s.get("name", "") for s in scenarios}
                    new_ones = [s for s in amp_scenarios if s.get("name", "") not in existing_names and s.get("name", "")]
                    if new_ones:
                        scenarios.extend(new_ones)
            except Exception as amp_err:
                import sys
                print(f"[AMPLIFICATION WARN] Coverage amplification failed: {type(amp_err).__name__}: {amp_err}", file=sys.stderr)

        duplicate_result = self.duplicate_detector.check(scenarios, registry.get_all())

        if req.scenario_actions:
            resolved = self.duplicate_detector.resolve_actions(
                scenarios, registry.get_all(),
                [sa.model_dump() if hasattr(sa, 'model_dump') else sa for sa in req.scenario_actions]
            )
            write_scenarios = resolved["to_add"] + resolved["to_override"]
            if resolved["to_remove"]:
                for entry in resolved["to_remove"]:
                    registry.delete(entry.get("id", ""))
            action_source = "user_resolved"
        else:
            action_source = "auto"
            write_scenarios = duplicate_result.get("unique_scenarios", scenarios)

        organization = await self.organization_agent.classify(context, feature_name)
        module = organization.get("module", "general")

        fname = feature_name or module
        context["page_object_module"] = module
        context["page_object_class"] = f"{fname.replace(' ', '').title().replace('-', '').replace('_', '')}Page"
        context["page_object_file"] = f"{fname.replace(' ', '_').lower()}_page"

        # Pass ALL locators and page_locators to the test agent so it can generate
        # tests for every page/module, not just the single classified module.
        test_locators = locators
        context["all_page_locators"] = page_locators

        test_code = await self.test_agent.generate(context, write_scenarios, test_locators, organization, mode, test_file_name, test_plan)

        test_file_path = file_writer.write_test_file(test_code, "", fname)

        # Extract base URL (scheme + host) so per-page routes don't double up
        base_url_full = ""
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url_full = f"{parsed.scheme}://{parsed.netloc}"

        # Detect test users from the application codebase
        test_users = FileWriter._detect_test_users_from_codebase(codebase_path)

        # Write one page object per discovered page, with comprehensive tests
        page_test_files = []
        if page_locators:
            for page_name, page_locs in page_locators.items():
                if page_locs:
                    file_writer.write_page_object(page_locs, "", page_name)
                    ptf = file_writer.write_page_test_file(page_name, base_url_full, page_locators=page_locs, test_users=test_users)
                    page_test_files.append(ptf)
        else:
            file_writer.write_page_object(locators, "", fname)
            if base_url_full:
                ptf = file_writer.write_page_test_file(fname, base_url_full, page_locators=locators, test_users=test_users)
                page_test_files.append(ptf)

        if action_source == "user_resolved" and resolved.get("to_override"):
            reg_all = registry.get_all()
            override_names = [s.get("name", "") for s in resolved["to_override"]]
            reg_all = [e for e in reg_all if e.get("name", "") not in override_names]
            registry.save_all(reg_all)

        file_writer.update_registry(write_scenarios, test_file_path, url, feature_name)
        for ptf in page_test_files:
            file_writer.update_registry([
                {"name": os.path.splitext(os.path.basename(ptf))[0] + " page tests", "steps": "", "expected_result": ""}
            ], ptf, url, f"{feature_name or fname}-page")

        plan_file_path = file_writer.write_test_plan(test_plan, feature_name or fname)

        test_structure = parse_test_file(test_file_path)

        execution_result = None
        healing_result = None
        report_path = ""

        registry_entries = []
        for s in write_scenarios:
            raw_steps = s.get("steps", "")
            if isinstance(raw_steps, list):
                raw_steps = "\n".join(str(x) for x in raw_steps)
            registry_entries.append({
                "id": str(uuid.uuid4()),
                "name": s.get("name", ""),
                "steps": raw_steps,
                "expected_result": s.get("expected_result", ""),
                "test_file": test_file_path,
                "url": url,
                "feature_name": feature_name or "app",
                "created_at": datetime.now().isoformat(),
            })

        llm_errors = get_and_clear_llm_errors()
        return {
            "status": "success",
            "message": f"Generated {len(write_scenarios)} scenarios",
            "locators": locators,
            "page_locators": page_locators,
            "scenarios": write_scenarios,
            "test_file_path": test_file_path,
            "page_test_files": page_test_files,
            "execution_result": execution_result,
            "healing_result": healing_result,
            "registry_entries": registry_entries,
            "report_path": report_path,
            "duplicate_result": duplicate_result,
            "organization": organization,
            "test_plan": test_plan,
            "plan_file_path": plan_file_path,
            "test_structure": test_structure,
            "auto_run_available": True,
            "project_scaffold": scaffold_result,
            "llm_errors": llm_errors,
        }

    async def run_planner(self, req, output_dir=None):
        if not output_dir:
            output_dir = os.getenv("OUTPUT_DIR", "")
        llm_provider = getattr(req, "llm_provider", None) or None
        llm_api_key = getattr(req, "llm_api_key", None) or None
        llm_model = getattr(req, "llm_model", None) or None
        llm_max_tokens = getattr(req, "llm_max_tokens", 0) or 0
        if llm_provider or llm_api_key or llm_model or llm_max_tokens:
            configure_llm(provider=llm_provider, api_key=llm_api_key, model=llm_model, max_tokens=llm_max_tokens)
        get_and_clear_llm_errors()
        self.context_builder = ContextBuilder(output_dir)

        scaffolder = ProjectScaffolder(output_dir)

        context = await self.context_builder.build(req)
        url = req.url or context.get("resolved_url", "")
        codebase_path = getattr(req, "codebase_path", None)

        locators, page_locators = await self.locator_agent.generate(url, codebase_path, context.get("codebase_context", {}))

        test_plan = await self.planner_agent.create_plan(context, "fresh")

        llm_errors = get_and_clear_llm_errors()
        return {
            "status": "success",
            "message": "Test plan created",
            "test_plan": test_plan,
            "locators": locators,
            "page_locators": page_locators,
            "url": url,
            "llm_errors": llm_errors,
        }

    async def run_tests(self, test_file_name, url, test_names=None):
        result = await self.execution_agent.execute(test_file_name, url, test_names)
        return result
