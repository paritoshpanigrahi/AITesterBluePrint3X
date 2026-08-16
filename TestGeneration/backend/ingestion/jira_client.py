import os
import json


class JiraClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")

    def _build_headers(self):
        headers = {"Accept": "application/json"}
        if self.email and self.api_token:
            import base64
            creds = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        elif self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    async def _get(self, path):
        import httpx
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=self._build_headers())
            resp.raise_for_status()
            return resp.json()

    def _extract_text_from_adf(self, adf):
        if isinstance(adf, str):
            return adf
        texts = []
        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and "text" in node:
                    texts.append(node["text"])
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(adf)
        return "\n".join(texts) if texts else str(adf)

    async def fetch_ticket(self, ticket_id):
        if not ticket_id or not self.base_url:
            return ""
        try:
            data = await self._get(f"/rest/agile/1.0/issue/{ticket_id}")
            fields = data.get("fields", {})
            lines = [f"Jira Ticket: {ticket_id}"]
            lines.append(f"Summary: {fields.get('summary', 'N/A')}")
            desc = fields.get("description", "")
            lines.append(f"Description: {self._extract_text_from_adf(desc)}")
            lines.append(f"Status: {fields.get('status', {}).get('name', 'N/A')}")
            lines.append(f"Priority: {fields.get('priority', {}).get('name', 'N/A')}")
            assignee = fields.get("assignee")
            lines.append(f"Assignee: {assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'}")
            lines.append(f"Type: {fields.get('issuetype', {}).get('name', 'N/A')}")
            labels = fields.get("labels", [])
            if labels:
                lines.append(f"Labels: {', '.join(labels)}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching Jira ticket {ticket_id}: {str(e)}"

    async def fetch_sprint(self, sprint_id, project_key):
        if not sprint_id or not self.base_url:
            return ""
        try:
            data = await self._get(f"/rest/agile/1.0/sprint/{sprint_id}")
            lines = [f"Jira Sprint: {sprint_id}"]
            lines.append(f"Name: {data.get('name', 'N/A')}")
            lines.append(f"Goal: {data.get('goal', 'N/A')}")
            lines.append(f"State: {data.get('state', 'N/A')}")
            start = data.get("startDate", "")
            end = data.get("endDate", "")
            if start:
                lines.append(f"Start: {start}")
            if end:
                lines.append(f"End: {end}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching Jira sprint {sprint_id}: {str(e)}"

    async def fetch_project(self, project_key):
        if not project_key or not self.base_url:
            return ""
        try:
            data = await self._get(f"/rest/api/3/project/{project_key}")
            lines = [f"Jira Project: {project_key}"]
            lines.append(f"Name: {data.get('name', 'N/A')}")
            lines.append(f"Key: {data.get('key', 'N/A')}")
            desc = data.get("description", "")
            if isinstance(desc, str):
                lines.append(f"Description: {desc}")
            elif isinstance(desc, dict):
                lines.append(f"Description: {self._extract_text_from_adf(desc)}")
            lead = data.get("lead")
            if lead:
                lines.append(f"Lead: {lead.get('displayName', 'N/A')}")
            lines.append(f"Type: {data.get('projectTypeKey', 'N/A')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching Jira project {project_key}: {str(e)}"

    async def test_credentials(self):
        if not self.base_url:
            return {"ok": False, "message": "Jira URL not configured"}
        if not self.email and not self.api_token:
            return {"ok": False, "message": "No Jira credentials configured"}
        try:
            data = await self._get("/rest/api/3/myself")
            return {"ok": True, "message": f"Authenticated as {data.get('displayName', data.get('emailAddress', 'unknown'))}"}
        except Exception as e:
            return {"ok": False, "message": f"Jira auth failed: {str(e)}"}