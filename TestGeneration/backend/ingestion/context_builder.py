import os
import json
import re
from backend.ingestion.codebase_analyzer import CodebaseAnalyzer
from backend.ingestion.document_parser import DocumentParser
from backend.ingestion.confluence_client import ConfluenceClient
from backend.ingestion.jira_client import JiraClient
from backend.ingestion.openapi_parser import OpenApiParser
from backend.ingestion.intelligent_document_parser import IntelligentDocumentParser
from backend.services.crawler import Crawler


class ContextBuilder:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.crawler = Crawler()
        self.codebase_analyzer = CodebaseAnalyzer()
        self.document_parser = DocumentParser()
        self.intelligent_parser = IntelligentDocumentParser()
        self.confluence_client = ConfluenceClient()
        self.jira_client = JiraClient()
        self.openapi_parser = OpenApiParser()

    async def build(self, req):
        context = {
            "url": req.url or "",
            "requirement": req.requirement or "",
            "requirement_preview": "",
            "resolved_url": "",
            "sources_loaded": [],
            "codebase_context": {},
            "api_endpoints": [],
            "env_vars": {},
            "routes_found": 0,
            "elements_found": 0,
            "api_endpoints_found": 0,
            "inferred_base_url": "",
            "infer_mode": "none",
            "message": "Context built successfully",
            "feature_name": getattr(req, "feature_name", None),
            "test_file_name": getattr(req, "test_file_name", None),
        }

        if req.prd_file_path and os.path.isfile(req.prd_file_path):
            try:
                text = self.document_parser.parse(req.prd_file_path)
                if text:
                    context["requirement"] += "\n" + text
                    context["sources_loaded"].append(f"PRD: {req.prd_file_path}")
            except Exception:
                pass

        if req.manual_tests_path and os.path.isfile(req.manual_tests_path):
            try:
                text = self.document_parser.parse(req.manual_tests_path)
                if text:
                    context["requirement"] += "\nManual Tests:\n" + text
                    context["sources_loaded"].append(f"Manual Tests: {req.manual_tests_path}")
            except Exception:
                pass

        if req.env_file_path and os.path.isfile(req.env_file_path):
            try:
                with open(req.env_file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            context["env_vars"][k.strip()] = v.strip()
                context["sources_loaded"].append(f"Env File: {req.env_file_path}")
            except Exception:
                pass

        if req.openapi_path and os.path.isfile(req.openapi_path):
            try:
                endpoints = self.openapi_parser.parse(req.openapi_path)
                if endpoints:
                    context["api_endpoints"].extend(endpoints)
                    context["sources_loaded"].append(f"OpenAPI: {req.openapi_path}")
            except Exception:
                pass

        if req.confluence_url:
            try:
                text = await self.confluence_client.fetch(req.confluence_url)
                if text:
                    context["requirement"] += "\n" + text
                    context["sources_loaded"].append(f"Confluence: {req.confluence_url}")
            except Exception:
                pass

        if req.jira_ticket_id:
            try:
                text = await self.jira_client.fetch_ticket(req.jira_ticket_id)
                if text:
                    context["requirement"] += "\n" + text
                    context["sources_loaded"].append(f"Jira Ticket: {req.jira_ticket_id}")
            except Exception:
                pass

        if req.jira_sprint_id:
            try:
                text = await self.jira_client.fetch_sprint(req.jira_sprint_id, req.jira_project_key)
                if text:
                    context["requirement"] += "\n" + text
                    context["sources_loaded"].append(f"Jira Sprint: {req.jira_sprint_id}")
            except Exception:
                pass

        if req.jira_project_key:
            try:
                text = await self.jira_client.fetch_project(req.jira_project_key)
                if text:
                    context["requirement"] += "\n" + text
                    context["sources_loaded"].append(f"Jira Project: {req.jira_project_key}")
            except Exception:
                pass

        if req.codebase_path and os.path.isdir(req.codebase_path):
            try:
                analysis = self.codebase_analyzer.analyze(req.codebase_path)
                if analysis:
                    context["codebase_context"] = analysis
                    context["routes_found"] = len(analysis.get("routes", []))
                    context["elements_found"] = len(analysis.get("element_hints", []))
                    context["inferred_base_url"] = analysis.get("inferred_base_url", "")
                    context["infer_mode"] = "codebase"
                    context["sources_loaded"].append(f"Codebase: {req.codebase_path}")
                    # Build explicit detected pages list from routes for downstream agents
                    routes = analysis.get("routes", [])
                    seen_segments = set()
                    detected = []
                    for r in routes:
                        if isinstance(r, str) and r.startswith("/"):
                            segments = [s for s in r.strip("/").split("/") if s and "{" not in s and ":" not in s]
                            for seg in segments:
                                s = seg.lower()
                                if s not in seen_segments and not s.startswith("_") and "." not in s:
                                    seen_segments.add(s)
                                    detected.append({"name": s.title(), "route": r, "matched_on": seg})
                    if detected:
                        context["detected_pages"] = detected
                    context["infer_mode"] = "codebase"
            except Exception:
                pass

        if req.url:
            context["resolved_url"] = req.url
            try:
                dom = await self.crawler.crawl(req.url)
                if dom and len(dom) > 100:
                    context["elements_found"] = dom.count("{") + dom.count("tag")
                    context["sources_loaded"].append(f"URL: {req.url}")
                    context["dom_snapshot"] = dom
                    context["crawled_content"] = dom
            except Exception:
                pass

        if context["api_endpoints"]:
            context["api_endpoints_found"] = len(context["api_endpoints"])

        preview = context["requirement"]
        if len(preview) > 200:
            preview = preview[:200] + "..."
        context["requirement_preview"] = preview

        return context
