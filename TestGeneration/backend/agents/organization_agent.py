import re
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm, extract_json


class OrganizationAgent:
    MODULES = ["auth", "checkout", "user-profile", "admin", "search", "onboarding", "notifications", "reports", "api", "marketing", "general"]
    TEST_TYPES = ["smoke", "regression", "e2e", "integration"]
    PRIORITIES = ["critical", "high", "medium", "low"]

    def __init__(self):
        self.skill = load_skill("organization_agent")

    async def classify(self, context, feature_name=None):
        requirement = context.get("requirement", "") or context.get("requirement_preview", "")
        url = context.get("url", "") or context.get("resolved_url", "")

        system_prompt = self.skill
        user_prompt = f"""
Feature Name: {feature_name or 'Untitled'}
URL: {url}
Requirement: {requirement[:8000]}

Classify this feature and return JSON:
{{"module": "", "test_type": "", "priority": "", "subdirectory": "", "tags": [], "reasoning": ""}}
"""
        try:
            content = await call_llm(system_prompt, user_prompt)
            result = extract_json(content)
            result["module"] = self._validate_module(result.get("module", "general"))
            result["test_type"] = self._validate_test_type(result.get("test_type", "e2e"))
            result["priority"] = self._validate_priority(result.get("priority", "medium"))
            return result
        except Exception:
            return self._fallback(feature_name, requirement, url)

    def _validate_module(self, module):
        module = (module or "general").lower().strip().replace(" ", "-")
        if module in self.MODULES:
            return module
        for m in self.MODULES:
            if m in module:
                return m
        return "general"

    def _validate_test_type(self, test_type):
        test_type = (test_type or "e2e").lower().strip()
        if test_type in self.TEST_TYPES:
            return test_type
        for t in self.TEST_TYPES:
            if t in test_type:
                return t
        return "e2e"

    def _validate_priority(self, priority):
        priority = (priority or "medium").lower().strip()
        if priority in self.PRIORITIES:
            return priority
        for p in self.PRIORITIES:
            if p in priority:
                return p
        return "medium"

    def _fallback(self, feature_name, requirement, url):
        fname = (feature_name or "").lower()
        req = (requirement or "").lower()
        module = "general"
        for m in self.MODULES:
            if m in fname or m in req:
                module = m
                break
        test_type = "e2e"
        if "smoke" in req or "sanity" in req:
            test_type = "smoke"
        elif "api" in req or "endpoint" in req:
            test_type = "integration"
        priority = "medium"
        for kw in ["critical", "urgent", "security", "payment"]:
            if kw in req:
                priority = "critical"
                break
        if "important" in req or "high" in req:
            priority = "high"
        tags = [f"@{module}", f"@{test_type}", f"@{priority}"]
        if fname:
            tags.append(f"@{fname.replace(' ', '-')}")
        return {
            "module": module,
            "test_type": test_type,
            "priority": priority,
            "subdirectory": module,
            "tags": tags,
            "reasoning": f"Auto-classified based on keywords: module={module}, type={test_type}, priority={priority}",
        }
