import json
import os
import uuid
from datetime import datetime
import re

from backend.agents.manual_test_agent import ManualTestAgent
from backend.agents._client_factory import configure as configure_llm
from backend.ingestion.context_builder import ContextBuilder


class ManualTestService:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.agent = ManualTestAgent()
        self.context_builder = ContextBuilder(output_dir)

    async def handle_request(self, req):
        llm_provider = getattr(req, "llm_provider", "") or ""
        llm_api_key = getattr(req, "llm_api_key", "") or ""
        llm_model = getattr(req, "llm_model", "") or ""
        llm_max_tokens = getattr(req, "llm_max_tokens", 0) or 0
        if llm_provider or llm_api_key or llm_model or llm_max_tokens:
            configure_llm(provider=llm_provider, api_key=llm_api_key, model=llm_model, max_tokens=llm_max_tokens)

        context = await self.context_builder.build(req)
        feature_name = req.feature_name or context.get("feature_name", "Untitled")
        feature_slug = self._slugify(feature_name)

        mode = req.mode
        existing_cases = None
        existing_file = None

        if mode in ("add", "edit"):
            existing_file = self._find_suite_file(feature_slug)
            if existing_file and os.path.isfile(existing_file):
                with open(existing_file, "r") as f:
                    suite = json.load(f)
                existing_cases = suite.get("test_cases", [])

        new_cases = await self.agent.generate(context, mode, existing_cases)

        if mode == "add" and existing_cases:
            existing_titles = {c.get("title", "") for c in existing_cases}
            unique_new = [c for c in new_cases if c.get("title", "") not in existing_titles]
            all_cases = existing_cases + unique_new
            added = len(unique_new)
            edited = 0
        elif mode == "edit" and existing_cases:
            case_map = {c.get("id", c.get("title", "")): c for c in existing_cases}
            for c in new_cases:
                cid = c.get("id", c.get("title", ""))
                if cid in case_map:
                    case_map[cid] = c
            all_cases = list(case_map.values())
            added = len(new_cases)
            edited = len(new_cases)
        else:
            all_cases = new_cases
            added = len(new_cases)
            edited = 0

        suite = {
            "feature_name": feature_name,
            "feature_slug": feature_slug,
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "test_cases": all_cases,
        }

        manual_dir = os.path.join(self.output_dir, "manual-tests")
        os.makedirs(manual_dir, exist_ok=True)
        file_path = os.path.join(manual_dir, f"{feature_slug}.json")
        with open(file_path, "w") as f:
            json.dump(suite, f, indent=2)

        return {
            "status": "success",
            "message": f"Generated {len(all_cases)} test cases",
            "feature_name": feature_name,
            "feature_slug": feature_slug,
            "mode": mode,
            "file_path": file_path,
            "test_cases": all_cases,
            "added_count": added,
            "edited_count": edited,
            "total_count": len(all_cases),
        }

    def list_suites(self):
        manual_dir = os.path.join(self.output_dir, "manual-tests")
        if not os.path.isdir(manual_dir):
            return []
        suites = []
        for fname in sorted(os.listdir(manual_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(manual_dir, fname)
                try:
                    with open(fpath, "r") as f:
                        suite = json.load(f)
                    suites.append({
                        "feature_name": suite.get("feature_name", ""),
                        "feature_slug": suite.get("feature_slug", ""),
                        "version": suite.get("version", ""),
                        "created_at": suite.get("created_at", ""),
                        "updated_at": suite.get("updated_at", ""),
                        "test_count": len(suite.get("test_cases", [])),
                        "file_path": fpath,
                    })
                except Exception:
                    pass
        return suites

    def get_suite(self, slug):
        manual_dir = os.path.join(self.output_dir, "manual-tests")
        fpath = os.path.join(manual_dir, f"{slug}.json")
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                return json.load(f)
        return None

    def _find_suite_file(self, slug):
        manual_dir = os.path.join(self.output_dir, "manual-tests")
        fpath = os.path.join(manual_dir, f"{slug}.json")
        if os.path.isfile(fpath):
            return fpath
        return None

    def _slugify(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')
