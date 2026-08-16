import json
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm, extract_json


class PlannerAgent:
    def __init__(self):
        self.skill = load_skill("planner_agent")

    async def create_plan(self, context, mode="fresh"):
        requirement = context.get("requirement", "") or context.get("requirement_preview", "")
        url = context.get("url", "") or context.get("resolved_url", "")
        codebase = context.get("codebase_context", {})
        routes = codebase.get("routes", []) if isinstance(codebase, dict) else context.get("routes", [])
        api_endpoints = codebase.get("api_endpoints", []) if isinstance(codebase, dict) else context.get("api_endpoints", [])
        dom_snapshot = context.get("dom_snapshot", "") or context.get("crawled_content", "")
        pages = context.get("pages", [])
        detected_pages = context.get("detected_pages", [])
        jira_context = context.get("jira_context", {})
        confluence_context = context.get("confluence_context", {})
        openapi_context = context.get("openapi_context", "")
        locators = context.get("locators", {}) or {}
        page_locators = context.get("page_locators", {}) or {}

        locators_text = ""
        if locators:
            locators_text = "\n".join(
                f"  {k}: primary={v.get('primary', '')}"
                for k, v in locators.items()
                if isinstance(v, dict)
            )[:4000]
        pages_text = ""
        if page_locators:
            parts = []
            for pn, pl in page_locators.items():
                if not isinstance(pl, dict):
                    continue
                parts.append(f"  [{pn}]")
                for lk, lv in list(pl.items())[:15]:
                    if isinstance(lv, dict):
                        parts.append(f"    {lk}: {lv.get('primary', '')}")
                parts.append("")
            pages_text = "\n".join(parts)[:4000]

        system_prompt = self.skill

        user_prompt = f"""
Mode: {mode}
URL: {url or 'Not provided'}

Requirement:
{requirement[:8000] if requirement else 'No explicit requirement provided. Infer from available context.'}

DOM Snapshot (key elements):
{dom_snapshot[:4000] if dom_snapshot else 'Not available'}

Discovered Interactive Elements (Locators):
{locators_text if locators_text else 'No locators detected'}

Pages and their elements:
{pages_text if pages_text else 'No pages detected'}

Codebase Analysis:
- Routes: {', '.join(routes[:30]) if routes else 'None detected'}
- API Endpoints: {', '.join(api_endpoints[:30]) if api_endpoints else 'None detected'}
- Detected Pages: {', '.join(f'{p["name"]} ({p["route"]})' for p in detected_pages[:20]) if detected_pages else 'Not available'}

Jira Context:
{json.dumps(jira_context, indent=2) if jira_context else 'Not provided'}

Confluence Context:
{json.dumps(confluence_context, indent=2) if confluence_context else 'Not provided'}

OpenAPI Spec:
{openapi_context[:2000] if openapi_context else 'Not provided'}

        Create a comprehensive test plan for ALL pages of this web application.
For each page's elements, determine what FUNCTIONALITY they enable using these mappings:
- Inputs named "username" + "password" + button named "signIn" / "login" = Authentication
- Buttons named "addProduct" / "createItem" + input fields = CRUD / Data Creation
- Buttons named "edit" / "update" / "modify" = Data modification
- Buttons named "delete" / "remove" + confirmation = Deletion operations
- "cart" / "checkout" / "placeOrder" / "payment" buttons = E-commerce / Order flows
- "searchInput" + "searchButton" = Search functionality
- "logout" / "signOut" / "sign_out" = Session management / Logout
- "register" / "signUp" / "sign_up" = Registration / Sign up
- "select" / "dropdown" / "filter" = Filtering / Selection
- "upload" / "import" / "export" = File operations
- "confirm" / "cancel" / "dialog" = Modal / Dialog interactions
- "profile" / "settings" / "account" = User profile management
- "dashboard" / "report" / "chart" / "stat" = Reporting / Analytics
- "notification" / "alert" / "toast" = Notifications / Alerts
- "pagination" / "next" / "previous" = Pagination / Page navigation
Generate scenarios for EVERY functional area detected on each page.
Return a JSON object with the following structure:
{{
  "plan": {{
    "title": "Test Plan Title",
    "url": "URL",
    "overview": "Brief description of the application under test and testing approach",
    "user_flows": [
      {{
        "name": "Flow name",
        "description": "Description of the user journey",
        "critical": true/false
      }}
    ],
    "scenarios": [
      {{
        "id": "scenario-1",
        "suite": "Top-level test suite name (e.g., 'Authentication')",
        "title": "Scenario title",
        "priority": "critical/high/medium/low",
        "type": "happy path / negative / edge case / smoke / regression",
        "preconditions": "Starting state requirements",
        "steps": ["1. Step one", "2. Step two"],
        "expected_result": "What should happen",
        "success_criteria": ["Criterion 1"],
        "failure_conditions": ["Condition 1"],
        "tags": ["@module:auth", "@critical"]
      }}
    ],
    "coverage_summary": "Summary of what is covered",
    "assumptions": ["Assumption 1"],
    "risks": ["Risk 1"]
  }}
}}
"""
        try:
            content = await call_llm(system_prompt, user_prompt, temperature=0.3, timeout=600)
            result = extract_json(content)
            plan = result.get("plan", result)
            return plan
        except Exception as e:
            import sys
            print(f"[PLANNER WARN] First attempt failed ({type(e).__name__}: {e}), retrying with strict JSON instruction...", file=sys.stderr)
            try:
                strict_prompt = user_prompt + "\n\nIMPORTANT: Return ONLY a raw JSON object. No markdown, no code fences, no backticks, no explanations. Start with { and end with }."
                content = await call_llm(system_prompt, strict_prompt, temperature=0.2, timeout=600)
                result = extract_json(content)
                plan = result.get("plan", result)
                return plan
            except Exception as e2:
                print(f"[PLANNER ERROR] Retry also failed ({type(e2).__name__}: {e2}), using fallback.", file=sys.stderr)
                return self._fallback_plan(requirement, url, mode, locators, dom_snapshot)

    @staticmethod
    def _infer_functional_scenarios(locators, url):
        scenarios = []

        def _collect_names(locs):
            names = []
            for k, v in (locs or {}).items():
                names.append(k)
                if isinstance(v, dict):
                    p = v.get("primary", "")
                    if p:
                        names.append(p.lower())
            return names

        elem_names = _collect_names(locators)
        combined = " ".join(elem_names).lower()

        if any(x in combined for x in ["signin", "sign_in", "login", "username", "password"]):
            scenarios.append({
                "id": "scenario-auth-1", "suite": "Authentication",
                "title": "User logs in with valid credentials",
                "priority": "critical", "type": "happy path",
                "preconditions": "Application is accessible",
                "steps": ["1. Navigate to the login page", "2. Enter valid username and password", "3. Click Sign In button"],
                "expected_result": "User is logged in and redirected to dashboard",
                "success_criteria": ["Dashboard is displayed", "User name is visible"],
                "failure_conditions": ["Error message shown"],
                "tags": ["@module:auth", "@critical"],
            })
            scenarios.append({
                "id": "scenario-auth-2", "suite": "Authentication",
                "title": "User login fails with invalid credentials",
                "priority": "critical", "type": "negative",
                "preconditions": "Application is accessible",
                "steps": ["1. Navigate to the login page", "2. Enter invalid username or password", "3. Click Sign In button"],
                "expected_result": "Error message is displayed and user is not logged in",
                "success_criteria": ["Error message appears", "User stays on login page"],
                "failure_conditions": ["User is logged in without valid credentials"],
                "tags": ["@module:auth", "@negative"],
            })

        if any(x in combined for x in ["add", "create", "new"]):
            scenarios.append({
                "id": "scenario-crud-1", "suite": "Data Management",
                "title": "User creates a new item successfully",
                "priority": "high", "type": "happy path",
                "preconditions": "User is logged in and on the data entry page",
                "steps": ["1. Click Add/New button", "2. Fill in required fields", "3. Click Save/Submit button"],
                "expected_result": "New item is created and appears in the list",
                "success_criteria": ["Success message displayed", "Item visible in list"],
                "failure_conditions": ["Error on save", "Item not created"],
                "tags": ["@module:data", "@crud"],
            })

        if any(x in combined for x in ["edit", "update", "modify", "change"]):
            scenarios.append({
                "id": "scenario-crud-2", "suite": "Data Management",
                "title": "User edits an existing item",
                "priority": "high", "type": "happy path",
                "preconditions": "User is logged in and viewing an existing item",
                "steps": ["1. Click Edit button on an item", "2. Modify the fields", "3. Click Save"],
                "expected_result": "Item is updated with new values",
                "success_criteria": ["Changes are visible after save"],
                "failure_conditions": ["Changes are not saved"],
                "tags": ["@module:data", "@crud"],
            })

        if any(x in combined for x in ["delete", "remove", "trash"]):
            scenarios.append({
                "id": "scenario-crud-3", "suite": "Data Management",
                "title": "User deletes an item",
                "priority": "high", "type": "happy path",
                "preconditions": "User is logged in and viewing an item that can be deleted",
                "steps": ["1. Click Delete button on an item", "2. Confirm deletion in the dialog"],
                "expected_result": "Item is removed from the list",
                "success_criteria": ["Item disappears from list", "Success message shown"],
                "failure_conditions": ["Item still visible", "Error during deletion"],
                "tags": ["@module:data", "@crud"],
            })

        if any(x in combined for x in ["search", "filter", "query", "find"]):
            scenarios.append({
                "id": "scenario-search-1", "suite": "Search & Filters",
                "title": "User searches for items by keyword",
                "priority": "medium", "type": "happy path",
                "preconditions": "Application is accessible and contains data",
                "steps": ["1. Enter search term in the search box", "2. Click Search button or press Enter"],
                "expected_result": "Matching results are displayed",
                "success_criteria": ["Results match the search term", "No results message shown when no match"],
                "failure_conditions": ["Results do not match search"],
                "tags": ["@module:search", "@e2e"],
            })

        if any(x in combined for x in ["cart", "checkout", "placeorder", "order", "payment", "shipping"]):
            scenarios.append({
                "id": "scenario-checkout-1", "suite": "Checkout",
                "title": "User adds item to cart and completes purchase",
                "priority": "critical", "type": "happy path",
                "preconditions": "User is logged in and has items in cart",
                "steps": ["1. Navigate to cart", "2. Click Checkout", "3. Fill shipping details", "4. Select payment method", "5. Place order"],
                "expected_result": "Order is placed successfully and confirmation is shown",
                "success_criteria": ["Order confirmation displayed", "Order number generated"],
                "failure_conditions": ["Order fails", "Payment error", "Cart not cleared"],
                "tags": ["@module:checkout", "@critical"],
            })

        if any(x in combined for x in ["logout", "signout", "sign_out"]):
            scenarios.append({
                "id": "scenario-auth-3", "suite": "Authentication",
                "title": "User logs out successfully",
                "priority": "medium", "type": "happy path",
                "preconditions": "User is logged in",
                "steps": ["1. Click Logout/Sign Out button"],
                "expected_result": "User is logged out and redirected to login page",
                "success_criteria": ["Login page is displayed", "User cannot access protected pages"],
                "failure_conditions": ["User stays logged in"],
                "tags": ["@module:auth", "@e2e"],
            })

        if any(x in combined for x in ["register", "signup", "sign_up"]):
            scenarios.append({
                "id": "scenario-auth-4", "suite": "Authentication",
                "title": "New user registers successfully",
                "priority": "high", "type": "happy path",
                "preconditions": "Registration page is accessible",
                "steps": ["1. Navigate to registration page", "2. Fill in required details", "3. Submit registration form"],
                "expected_result": "Account is created and user is logged in",
                "success_criteria": ["Success message shown", "User redirected to dashboard"],
                "failure_conditions": ["Registration fails", "Duplicate account error"],
                "tags": ["@module:auth", "@e2e"],
            })

        if any(x in combined for x in ["upload", "import"]):
            scenarios.append({
                "id": "scenario-file-1", "suite": "File Operations",
                "title": "User uploads a file",
                "priority": "medium", "type": "happy path",
                "preconditions": "User is logged in",
                "steps": ["1. Navigate to the upload section", "2. Select a file", "3. Click Upload button"],
                "expected_result": "File is uploaded successfully",
                "success_criteria": ["File appears in the listing", "Upload success message shown"],
                "failure_conditions": ["Upload fails", "File not visible"],
                "tags": ["@module:files", "@e2e"],
            })

        if any(x in combined for x in ["export", "download"]):
            scenarios.append({
                "id": "scenario-file-2", "suite": "File Operations",
                "title": "User exports data",
                "priority": "medium", "type": "happy path",
                "preconditions": "User is logged in and data exists",
                "steps": ["1. Navigate to the data section", "2. Click Export/Download button", "3. Wait for download"],
                "expected_result": "File is downloaded with the expected data",
                "success_criteria": ["Download completes", "File contains correct data"],
                "failure_conditions": ["Download fails", "File is empty"],
                "tags": ["@module:files", "@e2e"],
            })

        if any(x in combined for x in ["profile", "settings", "account"]):
            scenarios.append({
                "id": "scenario-profile-1", "suite": "Profile & Settings",
                "title": "User updates profile settings",
                "priority": "medium", "type": "happy path",
                "preconditions": "User is logged in",
                "steps": ["1. Navigate to Profile/Settings", "2. Modify profile fields", "3. Click Save"],
                "expected_result": "Profile is updated successfully",
                "success_criteria": ["Success message shown", "Changes are reflected"],
                "failure_conditions": ["Changes not saved", "Error on save"],
                "tags": ["@module:profile", "@e2e"],
            })

        if any(x in combined for x in ["dashboard", "report", "chart", "stat"]):
            scenarios.append({
                "id": "scenario-dashboard-1", "suite": "Dashboard & Reports",
                "title": "User views dashboard widgets and data",
                "priority": "medium", "type": "smoke",
                "preconditions": "User is logged in",
                "steps": ["1. Navigate to Dashboard", "2. Verify all widgets and charts are visible", "3. Interact with any filters"],
                "expected_result": "Dashboard displays all data correctly",
                "success_criteria": ["All widgets load", "Data is current"],
                "failure_conditions": ["Widgets fail to load", "Data is stale"],
                "tags": ["@module:dashboard", "@smoke"],
            })

        if any(x in combined for x in ["select", "dropdown", "option"]):
            scenarios.append({
                "id": "scenario-ui-1", "suite": "UI Interactions",
                "title": "User selects an option from a dropdown",
                "priority": "low", "type": "happy path",
                "preconditions": "User is logged in and on a page with dropdowns",
                "steps": ["1. Click the dropdown", "2. Select an option from the list"],
                "expected_result": "Option is selected and any dependent content updates",
                "success_criteria": ["Dropdown shows selected value", "Page content updates if applicable"],
                "failure_conditions": ["Selection not applied", "Dropdown does not open"],
                "tags": ["@module:ui", "@e2e"],
            })

        if any(x in combined for x in ["notification", "alert", "toast", "message"]):
            scenarios.append({
                "id": "scenario-ui-2", "suite": "Notifications",
                "title": "User views and dismisses notifications",
                "priority": "low", "type": "happy path",
                "preconditions": "User is logged in and has notifications",
                "steps": ["1. Click notification bell/icon", "2. View notification list", "3. Click dismiss on a notification"],
                "expected_result": "Notifications are viewable and dismissible",
                "success_criteria": ["Notifications list opens", "Notifications can be dismissed"],
                "failure_conditions": ["Notifications not visible", "Cannot dismiss"],
                "tags": ["@module:notifications", "@e2e"],
            })

        if any(x in combined for x in ["pagination", "next", "previous", "page"]):
            scenarios.append({
                "id": "scenario-ui-3", "suite": "Pagination",
                "title": "User navigates paginated content",
                "priority": "low", "type": "happy path",
                "preconditions": "User is logged in and on a paginated list",
                "steps": ["1. Click Next page", "2. Click Previous page", "3. Click a specific page number"],
                "expected_result": "Content updates to show the correct page",
                "success_criteria": ["Page content changes", "Page indicator updates"],
                "failure_conditions": ["Content does not change", "Page indicator wrong"],
                "tags": ["@module:ui", "@e2e"],
            })

        if any(x in combined for x in ["cancel", "confirm"]):
            scenarios.append({
                "id": "scenario-ui-4", "suite": "Dialogs",
                "title": "User cancels an action in a confirmation dialog",
                "priority": "medium", "type": "negative",
                "preconditions": "User is logged in and performing an action that triggers confirmation",
                "steps": ["1. Perform a delete/remove action", "2. Click Cancel in the confirmation dialog"],
                "expected_result": "Action is not performed and dialog closes",
                "success_criteria": ["Dialog closes", "No changes are made"],
                "failure_conditions": ["Action proceeds despite cancel", "Dialog does not close"],
                "tags": ["@module:ui", "@negative"],
            })

        return scenarios

    def _fallback_plan(self, requirement, url, mode, locators, dom_snapshot):
        scenarios = self._infer_functional_scenarios(locators, url)
        if not scenarios and requirement:
            lines = requirement.strip().split("\n") if requirement else []
            for i, line in enumerate(lines):
                line = line.strip()
                if line and len(line) > 10:
                    scenarios.append({
                        "id": f"scenario-{i+1}", "suite": "General",
                        "title": f"Test {i+1}: {line[:80]}",
                        "priority": "medium", "type": "happy path" if i == 0 else "edge case",
                        "preconditions": "Application is accessible",
                        "steps": [f"1. Navigate to {url or 'the application'}", f"2. {line}"],
                        "expected_result": "Operation completes successfully",
                        "success_criteria": ["Expected behavior is observed"],
                        "failure_conditions": ["Error is displayed"],
                        "tags": ["@general", "@e2e"],
                    })
        if not scenarios:
            scenarios.append({
                "id": "scenario-1", "suite": "General",
                "title": "Page loads and displays correctly",
                "priority": "medium", "type": "smoke",
                "preconditions": "Application is accessible",
                "steps": [f"1. Navigate to {url or 'the application'}", "2. Verify the page loads without errors"],
                "expected_result": "Page loads successfully",
                "success_criteria": ["Page loads without errors"],
                "failure_conditions": ["Page fails to load"],
                "tags": ["@general", "@smoke"],
            })
        return {
            "title": f"Test Plan for {url or 'Application'}",
            "url": url or "",
            "overview": f"Automated test plan generated from provided context in {mode} mode.",
            "user_flows": [{"name": "Main flow", "description": "Primary user journey through the application", "critical": True}],
            "scenarios": scenarios,
            "coverage_summary": f"Plan covers {len(scenarios)} scenarios across {len(set(s['suite'] for s in scenarios))} suites",
            "assumptions": ["Application is deployed and accessible"],
            "risks": ["URL or credentials may change over time"],
        }
