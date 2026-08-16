import os
import sys
import json
import shutil
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.utils.file_writer import FileWriter
from backend.models.schemas import (
    GenerateTestRequest, AddFeatureRequest, ModifyTestRequest, RunTestsRequest,
    ManualTestRequest, HealthResponse, ConfigResponse, ContextIngestResponse,
    GenerateTestResponse, ManualTestResponse, ExecutionResult,
    DuplicateCheckResult, HealingResult, TestGenerationResult,
    ManualTestSuite, ManualTestCase, SetupCheckResponse, SetupPlaywrightResponse,
)
from backend.orchestrator import Orchestrator
from backend.services.test_registry import TestRegistry
from backend.services.manual_test_service import ManualTestService
from backend.services.project_scaffolder import ProjectScaffolder
from backend.ingestion.context_builder import ContextBuilder
from backend.ingestion.jira_client import JiraClient
from backend.ingestion.confluence_client import ConfluenceClient

app = FastAPI(title="AI QA Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = int(os.getenv("PORT", "8765"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "")

orchestrator = Orchestrator()
registry = TestRegistry(OUTPUT_DIR)
manual_service = ManualTestService(OUTPUT_DIR)
context_builder = ContextBuilder(OUTPUT_DIR)

def get_output_dir():
    if not OUTPUT_DIR:
        return ""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR

def _sanitize_ascii(obj):
    if obj is None:
        return obj
    if isinstance(obj, str):
        return obj.encode("ascii", "ignore").decode("ascii")
    if isinstance(obj, dict):
        return {k: _sanitize_ascii(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_ascii(v) for v in obj]
    return obj



@app.get("/health")
async def health():
    return HealthResponse(status="ok", version="1.0.0")

@app.post("/test-atlassian-credentials")
async def test_atlassian_credentials():
    results = {}
    jc = JiraClient()
    cc = ConfluenceClient()
    results["jira"] = await jc.test_credentials()
    results["confluence"] = await cc.test_credentials()
    return results

@app.get("/config")
async def get_config():
    out = get_output_dir()
    return ConfigResponse(
        output_dir=out,
        resolved_path=os.path.abspath(out),
        tests_dir=os.path.join(out, "tests"),
        pages_dir=os.path.join(out, "pages"),
        reports_dir=os.path.join(out, "reports"),
    )

@app.post("/config")
async def update_config(body: dict):
    global OUTPUT_DIR, registry, manual_service, context_builder
    OUTPUT_DIR = body.get("output_dir", OUTPUT_DIR)
    os.environ["OUTPUT_DIR"] = OUTPUT_DIR
    registry = TestRegistry(OUTPUT_DIR)
    manual_service = ManualTestService(OUTPUT_DIR)
    context_builder = ContextBuilder(OUTPUT_DIR)
    out = get_output_dir()
    return ConfigResponse(
        output_dir=out,
        resolved_path=os.path.abspath(out),
        tests_dir=os.path.join(out, "tests"),
        pages_dir=os.path.join(out, "pages"),
        reports_dir=os.path.join(out, "reports"),
    )

@app.get("/browse-directories")
async def browse_directories(path: str = ""):
    try:
        if not path or path in (".", "~"):
            if os.name == "nt":
                import string
                drives = []
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drives.append({"name": drive, "path": drive, "is_dir": True})
                return {"path": "", "entries": drives, "parent": None, "error": ""}
            path = os.path.expanduser("~")
        else:
            path = os.path.expanduser(path)

        p = Path(path)
        if not p.is_dir():
            return {"path": str(p), "entries": [], "parent": None, "error": f"Not a directory: {path}"}

        current = str(p.resolve())
        entries = []
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                if child.is_dir() and not child.is_symlink():
                    entries.append({"name": child.name, "path": str(child), "is_dir": True})
            except (PermissionError, OSError):
                continue

        parent = str(p.parent) if p.parent != p else None
        return {"path": current, "entries": entries, "parent": parent, "error": ""}
    except Exception as e:
        return {"path": path or "", "entries": [], "parent": None, "error": str(e)}

@app.get("/check-setup")
async def check_setup():
    out_dir = get_output_dir()
    if not out_dir:
        return SetupCheckResponse(
            playwright_installed=False,
            npm_found=False,
            output_dir="",
            message="Output directory not configured. Set it in Settings first.",
        )
    scaffolder = ProjectScaffolder(out_dir)
    check = scaffolder.check()
    return SetupCheckResponse(
        playwright_installed=check.get("playwright_installed", False),
        npm_found=check.get("npm_found", False),
        output_dir=check.get("output_dir", ""),
        message=check.get("message", ""),
    )


@app.post("/setup-playwright")
async def setup_playwright():
    out_dir = get_output_dir()
    if not out_dir:
        return SetupPlaywrightResponse(
            status="error",
            message="Output directory not configured. Set it in Settings first.",
            scaffolded=False,
        )
    scaffolder = ProjectScaffolder(out_dir)
    check = scaffolder.check()
    if check.get("playwright_installed"):
        return SetupPlaywrightResponse(
            status="ok",
            message="Playwright project already exists",
            scaffolded=False,
        )
    result = scaffolder.ensure(user_consent=True)
    return SetupPlaywrightResponse(
        status="ok" if result.get("scaffolded") else "error",
        message=result.get("message", ""),
        scaffolded=result.get("scaffolded", False),
        npm_install=result.get("npm_install", ""),
        browser_install=result.get("browser_install", ""),
    )


@app.post("/ingest-context")
async def ingest_context(req: GenerateTestRequest) -> ContextIngestResponse:
    try:
        result = await context_builder.build(req)
        return ContextIngestResponse(
            sources_loaded=result.get("sources_loaded", []),
            requirement_preview=result.get("requirement_preview", ""),
            routes_found=result.get("routes_found", 0),
            elements_found=result.get("elements_found", 0),
            api_endpoints_found=result.get("api_endpoints_found", 0),
            inferred_base_url=result.get("inferred_base_url", ""),
            resolved_url=result.get("resolved_url", ""),
            infer_mode=result.get("infer_mode", "none"),
            message=result.get("message", "Context built"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-tests")
async def generate_tests(req: GenerateTestRequest):
    try:
        out_dir = req.output_dir or get_output_dir()
        if not out_dir:
            raise HTTPException(status_code=400, detail="Output directory not configured. Set it in Settings.")
        result = await orchestrator.run(req, "fresh", output_dir=out_dir)
        if result.get("status") == "setup_required":
            return result
        try:
            return GenerateTestResponse(**result)
        except Exception as ve:
            import sys; print(f"[API WARN] Pydantic validation failed, returning raw result: {ve}", file=sys.stderr)
            return result
    except HTTPException:
        raise
    except Exception as e:
        import sys; print(f"[API ERROR] {traceback.format_exc()}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-feature")
async def add_feature(req: AddFeatureRequest):
    try:
        out_dir = req.output_dir or get_output_dir()
        if not out_dir:
            raise HTTPException(status_code=400, detail="Output directory not configured. Set it in Settings.")
        result = await orchestrator.run(req, "add", feature_name=req.feature_name, output_dir=out_dir)
        try:
            return GenerateTestResponse(**result)
        except Exception as ve:
            import sys; print(f"[API WARN] Pydantic validation failed (add-feature), returning raw: {ve}", file=sys.stderr)
            return result
    except HTTPException:
        raise
    except Exception as e:
        import sys; print(f"[API ERROR] {traceback.format_exc()}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modify-tests")
async def modify_tests(req: ModifyTestRequest):
    try:
        out_dir = req.output_dir or get_output_dir()
        if not out_dir:
            raise HTTPException(status_code=400, detail="Output directory not configured. Set it in Settings.")
        result = await orchestrator.run(req, "modify", test_file_name=req.test_file_name, output_dir=out_dir)
        try:
            return GenerateTestResponse(**result)
        except Exception as ve:
            import sys; print(f"[API WARN] Pydantic validation failed (modify-tests), returning raw: {ve}", file=sys.stderr)
            return result
    except HTTPException:
        raise
    except Exception as e:
        import sys; print(f"[API ERROR] {traceback.format_exc()}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-structure")
async def get_test_structure(file: str = ""):
    from backend.utils.test_parser import parse_test_file
    result = parse_test_file(file)
    return result


@app.post("/run-tests")
async def run_tests(req: RunTestsRequest):
    from backend.utils.file_writer import FileWriter
    try:
        result = await orchestrator.run_tests(req.test_file_name, req.url, req.test_names)
        out_dir = get_output_dir()
        fw = FileWriter(out_dir)
        feature = os.path.splitext(os.path.basename(req.test_file_name))[0]
        report_path = fw.write_report(result, feature)
        result["report_path"] = report_path
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preview-plan")
async def preview_plan(req: GenerateTestRequest):
    try:
        out_dir = req.output_dir or get_output_dir()
        if not out_dir:
            raise HTTPException(status_code=400, detail="Output directory not configured. Set it in Settings.")
        result = await orchestrator.run_planner(req, output_dir=out_dir)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual-tests")
async def create_manual_tests(req: ManualTestRequest) -> ManualTestResponse:
    try:
        result = await manual_service.handle_request(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manual-tests")
async def list_manual_tests():
    suites = manual_service.list_suites()
    return {"suites": suites}

@app.get("/manual-tests/{slug}")
async def get_manual_test(slug: str):
    suite = manual_service.get_suite(slug)
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite

@app.get("/registry")
async def get_registry():
    entries = registry.get_all()
    return {"entries": entries}

@app.delete("/registry/{entry_id}")
async def delete_registry_entry(entry_id: str):
    success = registry.delete(entry_id)
    return {"success": success}

@app.get("/reports")
async def list_reports():
    reports_dir = os.path.join(get_output_dir(), "reports")
    reports = []
    if os.path.isdir(reports_dir):
        for f in sorted(os.listdir(reports_dir), reverse=True):
            if f.endswith(".html"):
                reports.append({"filename": f, "path": os.path.join(reports_dir, f)})
    return {"reports": reports}

@app.get("/reports/{filename}")
async def get_report(filename: str):
    reports_dir = os.path.join(get_output_dir(), "reports")
    filepath = os.path.join(reports_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(filepath, media_type="text/html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    upload_dir = os.path.join(get_output_dir(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "path": filepath}

@app.post("/export-test-plan")
async def export_test_plan(body: dict):
    try:
        out_dir = body.get("output_dir") or get_output_dir()
        if not out_dir:
            raise HTTPException(status_code=400, detail="Output directory not configured. Set it in Settings or provide output_dir in the request.")
        plan = body.get("test_plan", {})
        feature_name = body.get("feature_name", "test-plan")
        fw = FileWriter(out_dir)
        filepath = fw.write_test_plan(plan, feature_name)
        return {"status": "ok", "filepath": filepath, "filename": os.path.basename(filepath)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plans")
async def list_plans():
    plans_dir = os.path.join(get_output_dir(), "plans")
    plans = []
    if os.path.isdir(plans_dir):
        for f in sorted(os.listdir(plans_dir), reverse=True):
            if f.endswith(".md"):
                plans.append({"filename": f, "path": os.path.join(plans_dir, f)})
    return {"plans": plans}

@app.get("/plans/{filename}")
async def get_plan(filename: str):
    plans_dir = os.path.join(get_output_dir(), "plans")
    filepath = os.path.join(plans_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Plan not found")
    return FileResponse(filepath, media_type="text/markdown", filename=filename)

@app.get("/models")
async def list_models():
    try:
        import os
        from openai import AsyncOpenAI
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            models = await client.models.list()
            return {"data": [{"id": m.id, "name": m.id, "vendor": "openai"} for m in models]}
    except Exception:
        pass
    fallback = [
        {"id": "gpt-4o", "name": "GPT-4o", "vendor": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "vendor": "openai"},
        {"id": "o3-mini", "name": "O3 Mini", "vendor": "openai"},
        {"id": "o4-mini", "name": "O4 Mini", "vendor": "openai"},
        {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "vendor": "anthropic"},
        {"id": "claude-3-7-sonnet", "name": "Claude 3.7 Sonnet", "vendor": "anthropic"},
        {"id": "claude-opus-4", "name": "Claude Opus 4", "vendor": "anthropic"},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "vendor": "google"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "vendor": "google"},
    ]
    return {"data": fallback}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=PORT, log_level="info")
