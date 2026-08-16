import json
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm
from backend.services.crawler import Crawler


class HealingAgent:
    def __init__(self):
        self.skill = load_skill("healing_agent")

    async def heal(self, broken_selectors, url):
        if not broken_selectors or not url:
            return {"healed": False, "healed_selectors": [], "unresolved_selectors": [], "updated_files": [], "message": "No broken selectors or URL provided"}

        crawler = Crawler()
        dom_snapshot = await crawler.crawl(url)

        system_prompt = self.skill
        user_prompt = f"""
URL: {url}

Broken Selectors:
{json.dumps(broken_selectors, indent=2)}

Current DOM Snapshot:
{dom_snapshot[:6000]}

Generate replacement selectors for each broken selector.
Return JSON: [{{"old": "...", "new": "...", "strategy": "..."}}]
"""
        try:
            content = await call_llm(system_prompt, user_prompt)
            content = content.replace("```json", "").replace("```", "").strip()
            healed = json.loads(content)
            if not isinstance(healed, list):
                healed = []
            return {
                "healed": len(healed) > 0,
                "healed_selectors": healed,
                "unresolved_selectors": [],
                "updated_files": [],
                "message": f"Healed {len(healed)} selectors",
            }
        except Exception as e:
            return {
                "healed": False,
                "healed_selectors": [],
                "unresolved_selectors": [b.get("selector", str(b)) for b in broken_selectors],
                "updated_files": [],
                "message": f"Healing failed: {str(e)}",
            }
