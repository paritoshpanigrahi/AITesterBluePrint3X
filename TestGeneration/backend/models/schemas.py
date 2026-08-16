from pydantic import BaseModel, field_validator
from typing import Optional, List, Any


class ScenarioAction(BaseModel):
    name: str
    action: str  # "add" | "skip" | "override" | "remove"


class GenerateTestRequest(BaseModel):
    url: Optional[str] = None
    requirement: Optional[str] = None
    steps: Optional[List[str]] = None
    prd_file_path: Optional[str] = None
    confluence_url: Optional[str] = None
    jira_ticket_id: Optional[str] = None
    jira_sprint_id: Optional[str] = None
    jira_project_key: Optional[str] = None
    codebase_path: Optional[str] = None
    openapi_path: Optional[str] = None
    env_file_path: Optional[str] = None
    manual_tests_path: Optional[str] = None
    scenario_actions: Optional[List[ScenarioAction]] = None
    setup_playwright: Optional[bool] = None
    output_dir: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_max_tokens: Optional[int] = None


class AddFeatureRequest(GenerateTestRequest):
    feature_name: str


class ModifyTestRequest(GenerateTestRequest):
    test_file_name: str


class RunTestsRequest(BaseModel):
    test_file_name: str
    url: str
    test_names: Optional[List[str]] = None


class ElementHint(BaseModel):
    name: str
    tag: Optional[str] = None
    data_testid: Optional[str] = None
    id: Optional[str] = None
    aria_label: Optional[str] = None
    name_attr: Optional[str] = None
    placeholder: Optional[str] = None
    text: Optional[str] = None
    route: Optional[str] = None


class CodebaseContext(BaseModel):
    routes: List[str] = []
    component_map: dict = {}
    element_hints: List[ElementHint] = []
    api_endpoints: List[str] = []
    inferred_base_url: Optional[str] = None
    framework: Optional[str] = None


class ProjectContext(BaseModel):
    url: Optional[str] = None
    requirement: Optional[str] = None
    mode: str = "fresh"
    codebase_context: Optional[CodebaseContext] = None
    api_endpoints: List[str] = []
    env_vars: dict = {}
    feature_name: Optional[str] = None
    test_file_name: Optional[str] = None


class OrganizationPlan(BaseModel):
    module: str
    test_type: str
    priority: str
    subdirectory: str
    tags: List[str]
    reasoning: str


class ElementLocator(BaseModel):
    name: str
    tag: Optional[str] = None
    text: Optional[str] = None
    id: Optional[str] = None
    name_attr: Optional[str] = None
    aria_label: Optional[str] = None
    data_testid: Optional[str] = None
    placeholder: Optional[str] = None
    primary: str
    fallbacks: List[str] = []
    source: Optional[str] = None


class Scenario(BaseModel):
    name: str
    steps: str
    expected_result: str

    @field_validator("steps", mode="before")
    @classmethod
    def coerce_steps_to_string(cls, v):
        if isinstance(v, list):
            return "\n".join(str(s) for s in v)
        return v


class RequirementParseResult(BaseModel):
    scenarios: List[Scenario]


class DuplicateMatch(BaseModel):
    new_scenario_name: str
    existing_id: str
    existing_name: str
    existing_feature: str
    existing_test_file: str
    name_similarity: float
    steps_similarity: float


class DuplicateCheckResult(BaseModel):
    has_duplicates: bool
    unique_scenarios: List[Scenario]
    duplicate_matches: List[DuplicateMatch]
    pending_actions: Optional[List[dict]] = None


class ExecutionResult(BaseModel):
    status: str  # success, failure, error
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    logs: str = ""
    screenshots: List[str] = []
    broken_selectors: List[dict] = []
    is_real_bug: bool = False
    failure_summary: str = ""
    message: str = ""


class HealingResult(BaseModel):
    healed: bool = False
    healed_selectors: List[dict] = []
    unresolved_selectors: List[str] = []
    updated_files: List[str] = []
    message: str = ""


class RegistryEntry(BaseModel):
    id: str
    name: str
    steps: str
    expected_result: str
    test_file: str
    url: str
    feature_name: str
    created_at: str


class TestGenerationResult(BaseModel):
    test_code: str
    test_file_path: str
    feature_name: str
    mode: str
    scenario_count: int


class TestPlanScenario(BaseModel):
    id: str
    suite: str
    title: str
    priority: str = "medium"
    type: str = "happy path"
    preconditions: str = ""
    steps: List[str] = []
    expected_result: str = ""
    success_criteria: List[str] = []
    failure_conditions: List[str] = []
    tags: List[str] = []


class TestPlan(BaseModel):
    title: str = ""
    url: str = ""
    overview: str = ""
    user_flows: List[dict] = []
    scenarios: List[TestPlanScenario] = []
    coverage_summary: str = ""
    assumptions: List[str] = []
    risks: List[str] = []


class LlmErrorInfo(BaseModel):
    type: str = ""
    message: str = ""
    suggestion: str = ""


class SetupCheckResponse(BaseModel):
    playwright_installed: bool = False
    npm_found: bool = False
    output_dir: str = ""
    message: str = ""


class GenerateTestResponse(BaseModel):
    status: str
    message: str
    locators: dict = {}
    page_locators: dict = {}
    scenarios: List[Scenario] = []
    test_file_path: str = ""
    page_test_files: List[str] = []
    execution_result: Optional[ExecutionResult] = None
    healing_result: Optional[HealingResult] = None
    registry_entries: List[RegistryEntry] = []
    report_path: str = ""
    duplicate_result: Optional[DuplicateCheckResult] = None
    organization: Optional[OrganizationPlan] = None
    test_plan: Optional[TestPlan] = None
    test_structure: Optional[dict] = None
    auto_run_available: bool = False
    setup_playwright_required: bool = False
    setup_check: Optional[SetupCheckResponse] = None
    llm_errors: List[LlmErrorInfo] = []


class ManualTestCase(BaseModel):
    id: str
    title: str
    feature: str
    priority: str
    test_type: str
    preconditions: str
    steps: str
    expected_result: str
    tags: List[str] = []
    status: str = "active"


class ManualTestSuite(BaseModel):
    feature_name: str
    feature_slug: str
    version: str
    created_at: str
    updated_at: str
    test_cases: List[ManualTestCase]


class ManualTestRequest(GenerateTestRequest):
    feature_name: str = ""
    mode: str = "fresh"
    existing_file: Optional[str] = None


class ManualTestResponse(BaseModel):
    status: str
    message: str
    feature_name: str
    feature_slug: str
    mode: str
    file_path: str
    test_cases: List[ManualTestCase]
    added_count: int = 0
    edited_count: int = 0
    total_count: int = 0


class ContextIngestResponse(BaseModel):
    sources_loaded: List[str] = []
    requirement_preview: str = ""
    routes_found: int = 0
    elements_found: int = 0
    api_endpoints_found: int = 0
    inferred_base_url: str = ""
    resolved_url: str = ""
    infer_mode: str = "none"
    message: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str


class SetupPlaywrightResponse(BaseModel):
    status: str
    message: str
    scaffolded: bool = False
    npm_install: str = ""
    browser_install: str = ""


class ConfigResponse(BaseModel):
    output_dir: str
    resolved_path: str
    tests_dir: str
    pages_dir: str
    reports_dir: str
