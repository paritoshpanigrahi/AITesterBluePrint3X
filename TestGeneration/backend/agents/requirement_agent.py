from backend.utils.skill_loader import load_skill, render_skill
from backend.agents._client_factory import call_llm, extract_json


class RequirementAgent:
    def __init__(self):
        self.skill = load_skill("requirement_agent")

    async def parse(self, context, mode="fresh"):
        requirement = context.get("requirement", "") or context.get("requirement_preview", "")
        codebase = context.get("codebase_context", {})
        routes = codebase.get("routes", []) if isinstance(codebase, dict) else []
        api_endpoints = codebase.get("api_endpoints", []) if isinstance(codebase, dict) else context.get("api_endpoints", [])
        locators = context.get("locators", {}) or {}
        page_locators = context.get("page_locators", {}) or {}
        dom_snapshot = context.get("dom_snapshot", "") or context.get("crawled_content", "")

        system_prompt = self.skill

        detected_pages = context.get("detected_pages", [])

        codebase_text = ""
        if routes:
            codebase_text += f"\nDetected Routes: {', '.join(routes[:20])}"
        if detected_pages:
            codebase_text += f"\nDetected Pages: {', '.join(f'{p["name"]} ({p["route"]})' for p in detected_pages[:20])}"
        if api_endpoints:
            codebase_text += f"\nAPI Endpoints: {', '.join(api_endpoints[:20])}"

        locators_text = ""
        if locators:
            locators_text = "\n".join(
                f"  {k}: {v.get('primary', '')}"
                for k, v in (list(locators.items())[:30])
                if isinstance(v, dict)
            )

        pages_text = ""
        if page_locators:
            parts = []
            for pn, pl in page_locators.items():
                if not isinstance(pl, dict):
                    continue
                parts.append(f"  [{pn}]")
                for lk, lv in list(pl.items())[:10]:
                    if isinstance(lv, dict):
                        parts.append(f"    {lk}: {lv.get('primary', '')}")
            pages_text = "\n".join(parts)[:3000]

        dom_text = dom_snapshot[:2000] if dom_snapshot else ""

        input_type_hint = context.get("input_type", "")
        type_instruction = ""
        if input_type_hint == "steps":
            type_instruction = "The user provided raw test steps. Analyze them: if they look like explicit step-by-step test steps, preserve them verbatim in the output scenarios. If they look like requirements text, convert them to Given/When/Then format."
        elif input_type_hint == "requirement":
            type_instruction = "The user provided requirements text. Convert them into structured Given/When/Then scenarios."

        user_prompt = f"""
Mode: {mode}
Input Source: {input_type_hint if input_type_hint else 'requirement text'}
{type_instruction}

Input Content:
{requirement if requirement else 'No input provided'}
{codebase_text}

All Pages & Interactive Elements:
{pages_text if pages_text else 'Only one page detected'}
{locators_text if locators_text else 'No specific elements detected'}

DOM Content:
{dom_text if dom_text else 'Not available'}

The application has MULTIPLE pages with their own elements. You MUST generate scenarios for EVERY page.
Look at the "All Pages & Interactive Elements" section carefully - each [PageName] block represents a distinct page/module that needs its own set of test scenarios.

For each page, determine what FUNCTIONALITY its elements enable:
- Inputs named "username" + "password" + button named "signIn" / "login" = Authentication
- Buttons named "addProduct" / "createItem" + input fields = CRUD / Data Creation
- Buttons named "delete" / "remove" + confirmation = Deletion operations
- "cart" / "checkout" / "placeOrder" / "payment" buttons = E-commerce / Order flows
- "searchInput" + "searchButton" = Search functionality
- "logout" / "signOut" / "sign_out" = Session management / Logout
- "register" / "signUp" / "sign_up" = Registration / Sign up
- "edit" / "update" / "modify" = Data modification
- "select" / "dropdown" / "filter" = Filtering / Selection
- "upload" / "import" / "export" = File operations
- "confirm" / "cancel" / "dialog" = Modal / Dialog interactions
- "profile" / "settings" / "account" = User profile management
- "dashboard" / "report" / "chart" / "stat" = Reporting / Analytics
- "notification" / "alert" / "toast" = Notifications / Alerts
- "pagination" / "next" / "previous" = Pagination / Page navigation

Generate comprehensive functional scenarios that test ALL real user workflows across ALL pages.
Include happy paths, negative tests, and edge cases. Do NOT generate only navigation scenarios.

If the user provided specific steps or requirements, follow those. If only a URL was given, infer ALL functionality from the elements above.

Return JSON: {{"scenarios": [{{"name": "", "steps": "", "expected_result": ""}}]}}
"""
        try:
            content = await call_llm(system_prompt, user_prompt, timeout=600)
            result = extract_json(content)
            return result.get("scenarios", [])
        except Exception as e:
            import sys
            print(f"[REQUIREMENT WARN] First attempt failed ({type(e).__name__}: {e}), retrying...", file=sys.stderr)
            try:
                strict_prompt = user_prompt + "\n\nIMPORTANT: Return ONLY a raw JSON object. No markdown, no code fences, no backticks."
                content2 = await call_llm(system_prompt, strict_prompt, timeout=600)
                result2 = extract_json(content2)
                return result2.get("scenarios", [])
            except Exception as e2:
                print(f"[REQUIREMENT ERROR] Retry also failed ({type(e2).__name__}: {e2}), using fallback.", file=sys.stderr)
                return self._fallback_scenarios(requirement, locators, page_locators)

    def _fallback_scenarios(self, requirement, locators=None, page_locators=None):
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
        for pn, pl in (page_locators or {}).items():
            elem_names.extend(_collect_names(pl))
            elem_names.append(pn)

        combined = " ".join(elem_names).lower()
        # Also check page names from page_locators keys
        page_names = " ".join(pn.lower() for pn in (page_locators or {}).keys())

        if any(x in combined for x in ["login", "username", "password", "signin", "sign_in"]) or "login" in page_names:
            scenarios.append({
                "name": "User logs in with valid credentials",
                "steps": "1. Navigate to the application\n2. Enter valid username\n3. Enter valid password\n4. Click Sign In button",
                "expected_result": "User is redirected to the dashboard",
            })
            scenarios.append({
                "name": "User login fails with invalid credentials",
                "steps": "1. Navigate to the application\n2. Enter a valid username\n3. Enter a wrong password\n4. Click Sign In button",
                "expected_result": "Error message is displayed, user stays on login page",
            })

        if any(x in combined for x in ["add", "create", "new"]):
            scenarios.append({
                "name": "User creates a new item",
                "steps": "1. Log in to the application\n2. Navigate to the data management section\n3. Click Add/New button\n4. Fill in the required input fields\n5. Click Save/Submit button",
                "expected_result": "New item is created successfully and appears in the list view",
            })

        if any(x in combined for x in ["edit", "update", "modify", "change"]):
            scenarios.append({
                "name": "User edits an existing item",
                "steps": "1. Log in to the application\n2. Navigate to the item list\n3. Click Edit button on a specific item\n4. Modify one or more field values\n5. Click Save button",
                "expected_result": "Item is updated with the new values and changes are persisted",
            })

        if any(x in combined for x in ["delete", "remove", "trash"]):
            scenarios.append({
                "name": "User deletes an existing item",
                "steps": "1. Log in to the application\n2. Navigate to the item list\n3. Click Delete button on an item\n4. Confirm the deletion in the confirmation dialog",
                "expected_result": "Item is permanently removed from the list and a success message is shown",
            })

        if any(x in combined for x in ["search", "filter", "query", "find"]):
            scenarios.append({
                "name": "User searches for items by keyword",
                "steps": "1. Log in to the application\n2. Navigate to the search section\n3. Type a keyword in the search input\n4. Click Search button or press Enter",
                "expected_result": "Matching results are displayed in the list",
            })
            scenarios.append({
                "name": "Search returns no results for unmatched query",
                "steps": "1. Log in to the application\n2. Navigate to the search section\n3. Type a non-existent keyword\n4. Click Search button or press Enter",
                "expected_result": "No results message is displayed",
            })

        if any(x in combined for x in ["cart", "checkout", "placeorder", "payment", "shipping", "order"]):
            scenarios.append({
                "name": "User adds item to cart and completes purchase",
                "steps": "1. Log in to the application\n2. Browse products and click Add to Cart on an item\n3. Navigate to the cart page\n4. Verify the item appears in the cart\n5. Click Checkout / Place Order\n6. Fill in shipping details\n7. Select a payment method\n8. Confirm the order",
                "expected_result": "Order is placed successfully, confirmation page is shown, and order number is generated",
            })

        if any(x in combined for x in ["logout", "signout", "sign_out"]):
            scenarios.append({
                "name": "User logs out successfully",
                "steps": "1. Log in to the application\n2. Click the Logout / Sign Out button in the navigation",
                "expected_result": "User is logged out and redirected to the login page. Protected pages are no longer accessible.",
            })

        if any(x in combined for x in ["register", "signup", "sign_up"]):
            scenarios.append({
                "name": "New user creates an account",
                "steps": "1. Navigate to the registration / sign up page\n2. Fill in the required registration fields\n3. Submit the registration form",
                "expected_result": "Account is created successfully and user is logged in or redirected to login",
            })

        if any(x in combined for x in ["upload", "import"]):
            scenarios.append({
                "name": "User uploads a file",
                "steps": "1. Log in to the application\n2. Navigate to the upload section\n3. Select a file to upload\n4. Click Upload / Import button",
                "expected_result": "File is uploaded successfully and appears in the file list",
            })

        if any(x in combined for x in ["export", "download"]):
            scenarios.append({
                "name": "User exports data",
                "steps": "1. Log in to the application\n2. Navigate to the data section\n3. Select export options if applicable\n4. Click Export / Download button",
                "expected_result": "File is downloaded with the expected data",
            })

        if any(x in combined for x in ["select", "dropdown", "option"]):
            scenarios.append({
                "name": "User selects an option from a dropdown",
                "steps": "1. Log in to the application\n2. Locate the dropdown / select element\n3. Click to open the dropdown\n4. Select an option from the list",
                "expected_result": "The selected option is displayed and any dependent content updates accordingly",
            })

        if any(x in combined for x in ["profile", "settings", "account"]):
            scenarios.append({
                "name": "User updates their profile settings",
                "steps": "1. Log in to the application\n2. Navigate to Profile / Settings / Account page\n3. Modify one or more profile fields\n4. Click Save button",
                "expected_result": "Profile is updated successfully and changes are reflected immediately",
            })

        if any(x in combined for x in ["dashboard", "report", "chart", "stat"]):
            scenarios.append({
                "name": "User views the dashboard and its widgets",
                "steps": "1. Log in to the application\n2. Navigate to the Dashboard / Reports section\n3. Verify all dashboard widgets load correctly\n4. Interact with any filter or date range selector",
                "expected_result": "Dashboard displays correctly with all expected data widgets and charts",
            })

        if any(x in combined for x in ["notification", "alert", "toast", "message"]):
            scenarios.append({
                "name": "User interacts with notifications",
                "steps": "1. Log in to the application\n2. Trigger an action that generates a notification\n3. Click on the notification bell / icon\n4. View the notification list",
                "expected_result": "Notifications are displayed and can be read or dismissed",
            })

        if any(x in combined for x in ["pagination", "next", "previous", "page"]):
            scenarios.append({
                "name": "User navigates through paginated content",
                "steps": "1. Log in to the application\n2. Navigate to a section with multiple pages of data\n3. Click Next page button\n4. Click Previous page button\n5. Click a specific page number",
                "expected_result": "Content updates to show the correct page of results",
            })

        if any(x in combined for x in ["cancel", "confirm"]):
            scenarios.append({
                "name": "User cancels a pending action via confirmation dialog",
                "steps": "1. Log in to the application\n2. Perform an action that triggers a confirmation dialog\n3. Click Cancel in the dialog",
                "expected_result": "Action is not performed and dialog closes without side effects",
            })

        if not scenarios and requirement:
            lines = requirement.strip().split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if line and len(line) > 10:
                    scenarios.append({
                        "name": f"Test {i+1}: {line[:50]}",
                        "steps": f"1. Navigate to the application\n2. {line}",
                        "expected_result": "The operation completes successfully",
                    })
        if not scenarios:
            scenarios.append({
                "name": "Page loads and displays content correctly",
                "steps": "1. Navigate to the application URL\n2. Verify the page renders without errors\n3. Check that all expected elements are visible",
                "expected_result": "The page loads successfully with all elements rendered",
            })
        return scenarios
