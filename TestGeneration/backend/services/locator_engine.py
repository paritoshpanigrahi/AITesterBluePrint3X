from backend.agents.locator_agent import LocatorAgent


class LocatorEngine:
    def __init__(self):
        self.agent = LocatorAgent()

    async def generate_locators(self, url):
        return await self.agent.generate(url)

    async def generate_from_hints(self, url, element_hints):
        return await self.agent.generate_from_hints(url, element_hints)
