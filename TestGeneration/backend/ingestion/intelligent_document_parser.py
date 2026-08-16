from backend.ingestion.document_parser import DocumentParser
from backend.agents._client_factory import call_llm


class IntelligentDocumentParser:
    def __init__(self):
        self.base_parser = DocumentParser()

    async def parse_and_extract(self, filepath, extraction_type="requirements"):
        text = self.base_parser.parse(filepath)
        if not text:
            return None, "No text could be extracted"

        system_prompt = f"""You are an expert at extracting {extraction_type} from documents.
Extract all relevant information and return it as a structured summary."""

        user_prompt = f"""Extract {extraction_type} from the following document text.
Return a structured summary of what was found.

Document text:
{text[:6000]}"""

        try:
            result = await call_llm(system_prompt, user_prompt)
            return result, None
        except Exception as e:
            return text[:2000], str(e)

    async def analyze_requirements(self, filepath):
        return await self.parse_and_extract(filepath, "requirements and specifications")
