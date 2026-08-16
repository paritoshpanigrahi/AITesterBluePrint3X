from backend.agents.test_agent import TestAgent


class TestGenerator:
    def __init__(self):
        self.agent = TestAgent()

    async def generate(self, context, scenarios, locators, organization, mode="fresh", existing_file=None):
        return await self.agent.generate(context, scenarios, locators, organization, mode, existing_file)
