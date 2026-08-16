from backend.agents.healing_agent import HealingAgent


class HealingEngine:
    def __init__(self):
        self.agent = HealingAgent()

    async def heal_selectors(self, broken_selectors, url):
        result = await self.agent.heal(broken_selectors, url)
        return result

    async def patch_test_file(self, test_file_path, healed_selectors):
        if not test_file_path or not healed_selectors:
            return False
        try:
            with open(test_file_path, "r") as f:
                content = f.read()
            for h in healed_selectors:
                old = h.get("old", "")
                new = h.get("new", "")
                if old and new:
                    content = content.replace(old, new)
            with open(test_file_path, "w") as f:
                f.write(content)
            return True
        except Exception:
            return False
