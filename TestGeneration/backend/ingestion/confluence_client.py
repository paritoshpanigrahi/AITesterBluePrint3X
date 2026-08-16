import os


class ConfluenceClient:
    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
        self.email = os.getenv("CONFLUENCE_EMAIL", "")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN", "")

    def _build_headers(self):
        headers = {"User-Agent": "AI-QA-Platform/1.0"}
        if self.email and self.api_token:
            import base64
            creds = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        elif self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    async def fetch(self, url):
        if not url:
            return ""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self._build_headers())
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "lxml")
                    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    return text[:8000]
                return f"Failed to fetch Confluence page: HTTP {resp.status_code}"
        except Exception as e:
            return f"Error fetching Confluence: {str(e)}"

    async def test_credentials(self):
        if not self.base_url:
            return {"ok": False, "message": "Confluence URL not configured"}
        if not self.email and not self.api_token:
            return {"ok": False, "message": "No Confluence credentials configured"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                rest_url = self.base_url.rstrip("/wiki").rstrip("/") + "/wiki/rest/api/user/current"
                resp = await client.get(rest_url, headers=self._build_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    return {"ok": True, "message": f"Authenticated as {data.get('displayName', data.get('username', 'unknown'))}"}
                return {"ok": False, "message": f"Confluence auth failed: HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "message": f"Confluence auth error: {str(e)}"}