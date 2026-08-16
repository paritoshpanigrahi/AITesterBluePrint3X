import os
import json
import uuid
import re
from datetime import datetime


class FileWriter:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def write_test_file(self, code, module, feature_name):
        module_dir = os.path.join(self.output_dir, "tests", module)
        os.makedirs(module_dir, exist_ok=True)
        fname = f"{feature_name.replace(' ', '_').lower()}.spec.ts"
        fpath = os.path.join(module_dir, fname)
        lines = code.split("\n")
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            stripped = lines[i].strip()
            if not stripped:
                continue
            if stripped.startswith("```"):
                end_idx = i
                break
            # Reached actual code — keep everything including this line
            end_idx = i + 1
            break
        clean = "\n".join(lines[:max(end_idx, 1)])
        with open(fpath, "w") as f:
            f.write(clean.strip() + "\n")
        return fpath

    def write_page_object(self, locators, module, page_name):
        module_dir = os.path.join(self.output_dir, "pages", module)
        os.makedirs(module_dir, exist_ok=True)
        fname = f"{page_name.replace(' ', '_').lower()}_page.ts"
        fpath = os.path.join(module_dir, fname)

        class_name = f"{page_name.title().replace(' ', '').replace('-', '').replace('_', '')}Page"
        page_route = f"/{page_name}" if page_name and page_name != "app" else "/"

        lines = ['import { Page, Locator } from "@playwright/test";', ""]
        lines.append(f"export class {class_name} {{")
        lines.append("  readonly page: Page;")
        lines.append("")

        if isinstance(locators, dict):
            for name, loc in locators.items():
                if isinstance(loc, dict):
                    primary = loc.get("primary", "")
                    if primary:
                        locator_expr = self._parse_locator(primary)
                        lines.append(f"  get {name}(): Locator {{")
                        lines.append(f"    return {locator_expr};")
                        lines.append("  }")
                        lines.append("")

        lines.append("  constructor(page: Page) {")
        lines.append("    this.page = page;")
        lines.append("  }")
        lines.append("")

        lines.append("  async goto(url?: string) {")
        lines.append(f"    await this.page.goto(url || '{page_route}');")
        lines.append("  }")
        lines.append("")

        # Inject inferred action methods
        actions = self._infer_actions(locators)
        for action in actions:
            params = ", ".join(action["params"])
            lines.append(f"  async {action['name']}({params}) {{")
            for step in action["steps"]:
                lines.append(f"    {step}")
            lines.append("  }")
            lines.append("")

        lines.append("}")

        with open(fpath, "w") as f:
            f.write("\n".join(lines))
        return fpath

    @staticmethod
    def _detect_test_users_from_codebase(codebase_path):
        if not codebase_path or not os.path.isdir(codebase_path):
            return {}
        for candidate in ["src/data/mockData.js", "src/data/mockData.jsx", "src/data/users.js", "src/data/users.json"]:
            fpath = os.path.join(codebase_path, candidate)
            if os.path.isfile(fpath):
                break
        else:
            return {}
        try:
            with open(fpath, "r") as f:
                content = f.read()
        except Exception:
            return {}
        users_found = {}
        patterns = [
            r"username:\s*'(\w+)'[^}]*?password:\s*'(\w+)'[^}]*?role:\s*'(\w+)'[^}]*?status:\s*'(\w+)'",
            r'"username"\s*:\s*"(\w+)"[^}]*?"password"\s*:\s*"(\w+)"[^}]*?"role"\s*:\s*"(\w+)"[^}]*?"status"\s*:\s*"(\w+)"',
            r"'username'\s*:\s*'(\w+)'[^}]*?'password'\s*:\s*'(\w+)'[^}]*?'role'\s*:\s*'(\w+)'[^}]*?'status'\s*:\s*'(\w+)'",
        ]
        matches = []
        for p in patterns:
            matches = re.findall(p, content, re.DOTALL)
            if matches:
                break
        if not matches:
            simple_patterns = [
                r"username:\s*'(\w+)',\s*password:\s*'(\w+)'",
                r'"username":\s*"(\w+)",\s*"password":\s*"(\w+)"',
                r"'username':\s*'(\w+)',\s*'password':\s*'(\w+)'",
            ]
            for sp in simple_patterns:
                matches = re.findall(sp, content)
                if matches:
                    break
            for username, password in matches:
                label = "user" if "user" not in users_found else "alt"
                users_found[label] = {"username": username, "password": password}
            return users_found
        for username, password, role, status in matches:
            if role not in users_found:
                users_found[role] = {"username": username, "password": password, "status": status}
        return users_found

    def write_page_test_file(self, page_name, base_url, module="", page_locators=None, test_users=None):
        module_dir = os.path.join(self.output_dir, "tests", module)
        os.makedirs(module_dir, exist_ok=True)
        fname = f"{page_name.replace(' ', '_').lower()}.spec.ts"
        fpath = os.path.join(module_dir, fname)

        class_name = f"{page_name.title().replace(' ', '').replace('-', '').replace('_', '')}Page"
        po_import_path = f"../pages/{page_name.replace(' ', '_').lower()}_page"

        page_route = f"/{page_name}" if page_name and page_name != "app" else "/"
        base_url_clean = base_url.rstrip("/")

        if page_route == "/":
            url_pattern = ".*"
        else:
            url_pattern = page_route.replace("/", "\\/")

        if test_users is None:
            test_users = {}

        lines = [
            'import { test, expect } from "@playwright/test";',
            f'import {{ {class_name} }} from "{po_import_path}";',
            "",
            f'test.describe("{page_name.title()}", () => {{',
        ]

        has_url = bool(base_url)

        # 1. Page loads successfully (smoke)
        if has_url:
            lines.extend([
                f"  test('page loads successfully'",
                f'    , {{ tag: ["@{page_name.lower()}", "@smoke"] }}',
                f"    , async ({{ page }}) => {{",
                f"      const pageObj = new {class_name}(page);",
                f"      await pageObj.goto('{base_url_clean}{page_route}');",
                f"      await expect(page).toHaveURL(/{url_pattern}/);",
                "    });",
                "",
            ])

        if page_locators and isinstance(page_locators, dict) and len(page_locators) > 0:
            keys = list(page_locators.keys())

            # 2. All key elements are visible
            lines.extend([
                f"  test('all key elements are visible'",
                f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                f"    , async ({{ page }}) => {{",
                f"      const pageObj = new {class_name}(page);",
                f"      await pageObj.goto('{base_url_clean}{page_route}');",
            ])
            for name in keys:
                lines.append(f"      await expect(pageObj.{name}).toBeVisible();")
            lines.extend([
                "    });",
                "",
            ])

            # 3. Navigation from NavLink/Link hrefs
            nav_tests = self._build_nav_link_tests(page_locators, keys, class_name, base_url_clean, page_route, page_name)
            lines.extend(nav_tests)

            # 4. Input field fill tests
            input_fields = [n for n in keys if any(
                n.endswith(sfx) for sfx in ["Input", "input", "Field", "field"]
            )]
            for field_name in input_fields:
                display_name = re.sub(r'(Input|input|Field|field)$', '', field_name)
                display_name = re.sub(r'([A-Z])', r' \1', display_name).strip().lower()
                lines.extend([
                    f"  test('can type in {display_name}'",
                    f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                    f"    , async ({{ page }}) => {{",
                    f"      const pageObj = new {class_name}(page);",
                    f"      await pageObj.goto('{base_url_clean}{page_route}');",
                    f"      await expect(pageObj.{field_name}).toBeVisible();",
                    f"      await pageObj.{field_name}.fill('test value');",
                    f"      await expect(pageObj.{field_name}).toHaveValue('test value');",
                    "    });",
                    "",
                ])

            # 5. Button/link visibility tests (excluding NavLink/Link already tested in nav tests)
            nav_keys = {n for n in keys if n.endswith("NavLink") or n.endswith("Link")}
            clickable = [n for n in keys if any(
                n.endswith(sfx) for sfx in ["_button", "_btn", "Button", "Btn", "Link", "NavLink"]
            ) and n not in nav_keys]
            for btn_name in clickable:
                display_name = btn_name
                for sfx in ["_button", "_btn", "Button", "Btn", "Link", "NavLink"]:
                    if display_name.endswith(sfx):
                        display_name = display_name[:-len(sfx)]
                        break
                display_name = re.sub(r'([A-Z])', r' \1', display_name).strip().lower()
                lines.extend([
                    f"  test('{display_name} is visible and clickable'",
                    f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                    f"    , async ({{ page }}) => {{",
                    f"      const pageObj = new {class_name}(page);",
                    f"      await pageObj.goto('{base_url_clean}{page_route}');",
                    f"      await expect(pageObj.{btn_name}).toBeVisible();",
                    f"      await expect(pageObj.{btn_name}).toBeEnabled();",
                    "    });",
                    "",
                ])

            # 6. Action flow tests (generic, derived from locator patterns)
            actions = self._infer_actions(page_locators)
            has_login = any(a["name"] == "login" for a in actions)
            has_search = any(a["name"] == "search" for a in actions)
            has_create = any("add" in a["name"].lower() or "create" in a["name"].lower() or "new" in a["name"].lower() for a in actions)
            has_edit = any("edit" in a["name"].lower() or "update" in a["name"].lower() for a in actions)
            has_delete = any("delete" in a["name"].lower() or "remove" in a["name"].lower() for a in actions)
            has_select = any("filter" in a["name"].lower() or "select" in a["name"].lower() for a in actions)

            for action in actions:
                action_name = action["name"]
                display_action = re.sub(r'([A-Z])', r' \1', action_name).strip().lower()

                if action_name == "login":
                    creds = list(test_users.values()) if test_users else []
                    if creds:
                        valid_creds = creds[0]
                        lines.extend([
                            f"  test('can login with valid credentials'",
                            f'    , {{ tag: ["@{page_name.lower()}", "@regression", "@critical"] }}',
                            f"    , async ({{ page }}) => {{",
                            f"      const pageObj = new {class_name}(page);",
                            f"      await pageObj.goto('{base_url_clean}{page_route}');",
                            f"      await pageObj.login('{valid_creds['username']}', '{valid_creds['password']}');",
                            f"      await expect(page).not.toHaveURL(/{url_pattern}/);",
                            "    });",
                            "",
                        ])
                    # Invalid password - stays on same page (works for any login form)
                    lines.extend([
                        f"  test('shows error with invalid password'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.login('invaliduser', 'wrongpassword');",
                        f"      await expect(page).toHaveURL(/{url_pattern}/);",
                        "    });",
                        "",
                    ])
                    # Empty credentials validation (works for any login form)
                    submit_btn = None
                    for k in keys:
                        kl = k.lower()
                        if any(x in kl for x in ["sign", "login", "submit", "log_in"]):
                            submit_btn = k
                            break
                    if submit_btn:
                        lines.extend([
                            f"  test('stays on page with empty credentials'",
                            f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                            f"    , async ({{ page }}) => {{",
                            f"      const pageObj = new {class_name}(page);",
                            f"      await pageObj.goto('{base_url_clean}{page_route}');",
                            f"      await pageObj.{submit_btn}.click();",
                            f"      await expect(page).toHaveURL(/{url_pattern}/);",
                            "    });",
                            "",
                        ])
                elif action_name == "search":
                    lines.extend([
                        f"  test('can search for items'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.search('test query');",
                        f"      await expect(pageObj.{keys[0]}).toBeVisible();",
                        "    });",
                        "",
                    ])
                    lines.extend([
                        f"  test('search returns empty for unmatched query'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@negative"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.search('xyznonexistent12345');",
                        "    });",
                        "",
                    ])
                elif action_name == "logout":
                    lines.extend([
                        f"  test('can logout successfully'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@regression", "@auth"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.logout();",
                        f"      await expect(page).toHaveURL(/login/);",
                        "    });",
                        "",
                    ])
                elif has_create and ("save" in action_name.lower() or "submit" in action_name.lower()):
                    lines.extend([
                        f"  test('can save a new item with valid data'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@crud", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      // Fill form fields first",
                        f"      await pageObj.{action_name}();",
                        f"      await expect(pageObj.{keys[0]}).toBeVisible();",
                        "    });",
                        "",
                    ])
                elif has_edit and ("save" in action_name.lower() or "submit" in action_name.lower()):
                    lines.extend([
                        f"  test('can save edited item with changes'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@crud", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.{action_name}();",
                        f"      await expect(pageObj.{keys[0]}).toBeVisible();",
                        "    });",
                        "",
                    ])
                elif has_delete and ("confirm" in action_name.lower() or "delete" in action_name.lower()):
                    lines.extend([
                        f"  test('can delete an item after confirmation'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@crud", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                        f"      await pageObj.{action_name}();",
                        f"      await expect(pageObj.{keys[0]}).toBeVisible();",
                        "    });",
                        "",
                    ])
                else:
                    dummy_args = []
                    for param in action["params"]:
                        pname = param.split(":")[0].strip()
                        dummy_args.append(f"'test_{pname}'")
                    lines.extend([
                        f"  test('can {display_action}'",
                        f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                        f"    , async ({{ page }}) => {{",
                        f"      const pageObj = new {class_name}(page);",
                        f"      await pageObj.goto('{base_url_clean}{page_route}');",
                    ])
                    if dummy_args:
                        lines.append(f"      await pageObj.{action_name}({', '.join(dummy_args)});")
                    else:
                        lines.append(f"      await pageObj.{action_name}();")
                    lines.extend([
                        f"      await expect(pageObj.{keys[0]}).toBeVisible();",
                        "    });",
                        "",
                    ])

        lines.append("});")
        lines.append("")

        with open(fpath, "w") as f:
            f.write("\n".join(lines))
        return fpath

    def _build_nav_link_tests(self, page_locators, keys, class_name, base_url_clean, page_route, page_name):
        lines = []
        nav_link_keys = [n for n in keys if n.endswith("NavLink") or n.endswith("Link")]
        for key in nav_link_keys:
            loc = page_locators[key]
            primary = loc.get("primary", "") if isinstance(loc, dict) else ""
            href = self._extract_href(primary)
            if not href:
                continue
            display_name = key
            for sfx in ["NavLink", "Link"]:
                if display_name.endswith(sfx):
                    display_name = display_name[:-len(sfx)]
                    break
            display_name = re.sub(r'([A-Z])', r' \1', display_name).strip().lower()
            href_route = href.rstrip("/")
            if not href_route or href_route == "":
                href_pattern = ".*"
            else:
                href_pattern = href_route.replace("/", "\\/")
            lines.extend([
                f"  test('can navigate to {display_name}'",
                f'    , {{ tag: ["@{page_name.lower()}", "@regression"] }}',
                f"    , async ({{ page }}) => {{",
                f"      const pageObj = new {class_name}(page);",
                f"      await pageObj.goto('{base_url_clean}{page_route}');",
                f"      await pageObj.{key}.click();",
                f"      await expect(page).toHaveURL(/{href_pattern}/);",
                "    });",
                "",
            ])
        return lines

    @staticmethod
    def _extract_href(locator_str):
        m = re.search(r'''href=["']([^"']+)["']''', locator_str)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def _infer_actions(locators):
        keys = list(locators.keys()) if isinstance(locators, dict) else []
        actions = []

        def first_match(patterns):
            for k in keys:
                kl = k.lower()
                if any(p in kl for p in patterns):
                    return k
            return None

        # 1. Login action
        uname = first_match(["username"])
        email = first_match(["email", "mail"])
        pwd = first_match(["password", "passwd", "pass"])
        submit = first_match(["sign", "login", "submit", "log_in"])
        login_field = uname or email
        if login_field and pwd and submit:
            actions.append({
                "name": "login",
                "params": ["username: string", "password: string"],
                "steps": [
                    f"await this.{login_field}.fill(username);",
                    f"await this.{pwd}.fill(password);",
                    f"await this.{submit}.click();",
                ],
            })

        # 2. Search action
        search_field = first_match(["search", "query"])
        search_btn = None
        for k in keys:
            if "search" in k.lower() and ("btn" in k.lower() or "button" in k.lower()):
                search_btn = k
                break
        if search_field:
            steps = [f"await this.{search_field}.fill(query);"]
            if search_btn:
                steps.append(f"await this.{search_btn}.click();")
            else:
                steps.append(f'await this.{search_field}.press("Enter");')
            actions.append({"name": "search", "params": ["query: string"], "steps": steps})

        covered = set()
        for a in actions:
            for s in a["steps"]:
                m = re.search(r"this\.(\w+)", s)
                if m:
                    covered.add(m.group(1))

        # 3. Fill methods for remaining inputs
        for k in keys:
            if k in covered:
                continue
            if not (k.endswith("Input") or k.endswith("input") or k.endswith("Field") or k.endswith("field")):
                continue
            if "search" in k.lower() or "query" in k.lower() or "username" in k.lower() or "password" in k.lower() or "email" in k.lower():
                continue
            method_name = k
            for sfx in ["Input", "input", "Field", "field"]:
                if method_name.endswith(sfx):
                    method_name = method_name[: -len(sfx)]
                    break
            if not method_name:
                continue
            method_name = method_name[0].lower() + method_name[1:] if method_name else "fillField"
            if method_name in [a["name"] for a in actions]:
                method_name = "enter" + k[0].upper() + k[1:] if k else "enterField"
            actions.append({
                "name": method_name,
                "params": ["value: string"],
                "steps": [f"await this.{k}.fill(value);"],
            })
            covered.add(k)

        # 4. Click methods for remaining buttons/links
        for k in keys:
            if k in covered:
                continue
            if k == submit:
                continue
            is_clickable = any(
                k.endswith(sfx)
                for sfx in ["_button", "_btn", "Button", "Btn", "Link", "NavLink"]
            )
            if not is_clickable:
                continue
            method_name = k
            for sfx in ["_button", "_btn", "Button", "Btn", "Link", "NavLink"]:
                if method_name.endswith(sfx):
                    method_name = method_name[: -len(sfx)]
                    break
            if not method_name:
                continue
            if method_name in [a["name"] for a in actions]:
                method_name = "click" + k[0].upper() + k[1:] if k else "clickAction"
            actions.append({
                "name": method_name,
                "params": [],
                "steps": [f"await this.{k}.click();"],
            })
            covered.add(k)

        # 5. Detect logout action
        for k in keys:
            kl = k.lower()
            if any(x in kl for x in ["logout", "signout", "sign_out"]):
                if k not in covered:
                    actions.append({
                        "name": "logout",
                        "params": [],
                        "steps": [f"await this.{k}.click();"],
                    })
                    covered.add(k)

        # 6. Detect confirm/cancel actions from buttons
        confirm_btn = None
        cancel_btn = None
        for k in keys:
            kl = k.lower()
            if any(x in kl for x in ["confirm", "yes", "ok", "approve"]):
                confirm_btn = k
            elif any(x in kl for x in ["cancel", "no", "dismiss"]):
                cancel_btn = k
        if confirm_btn and confirm_btn not in covered:
            actions.append({
                "name": "confirmDialog",
                "params": [],
                "steps": [f"await this.{confirm_btn}.click();"],
            })
            covered.add(confirm_btn)
        if cancel_btn and cancel_btn not in covered:
            actions.append({
                "name": "cancelDialog",
                "params": [],
                "steps": [f"await this.{cancel_btn}.click();"],
            })
            covered.add(cancel_btn)

        return actions

    def write_test_plan(self, plan, feature_name="test-plan"):
        plans_dir = os.path.join(self.output_dir, "plans")
        os.makedirs(plans_dir, exist_ok=True)
        fname = f"{feature_name.replace(' ', '_').lower()}_test_plan.md"
        fpath = os.path.join(plans_dir, fname)

        md = self._test_plan_to_markdown(plan)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(md)
        return fpath

    @staticmethod
    def _test_plan_to_markdown(plan):
        if not plan:
            return "# Test Plan\n\nNo test plan generated.\n"

        lines = []
        title = plan.get("title", "Test Plan")
        lines.append(f"# {title}\n")

        url = plan.get("url", "")
        if url:
            lines.append(f"- **URL:** {url}")

        overview = plan.get("overview", "")
        if overview:
            lines.append(f"\n## Overview\n\n{overview}\n")

        user_flows = plan.get("user_flows", [])
        if user_flows:
            lines.append("## User Flows\n")
            for f in user_flows:
                name = f.get("name", "")
                desc = f.get("description", "")
                critical = f.get("critical", False)
                badge = " **Critical**" if critical else ""
                if desc:
                    lines.append(f"- **{name}** — {desc}{badge}")
                else:
                    lines.append(f"- **{name}**{badge}")
            lines.append("")

        scenarios = plan.get("scenarios", [])
        if scenarios:
            lines.append(f"## Scenarios ({len(scenarios)})\n")
            for i, s in enumerate(scenarios, 1):
                sid = s.get("id", f"scenario-{i}")
                title_s = s.get("title", f"Scenario {i}")
                suite = s.get("suite", "")
                priority = s.get("priority", "medium")
                stype = s.get("type", "happy path")
                lines.append(f"### {i}. {title_s}")
                tags = [t for t in [f"@{suite.lower().replace(' ', '-')}" if suite else "", f"@{priority}", f"@{stype.replace(' ', '-')}"] if t]
                lines.append(f"**ID:** `{sid}` | **Suite:** {suite} | **Priority:** {priority} | **Type:** {stype}\n")

                preconditions = s.get("preconditions", "")
                if preconditions:
                    lines.append(f"**Preconditions:** {preconditions}\n")

                steps = s.get("steps", [])
                if steps:
                    lines.append("**Steps:**\n")
                    for j, step in enumerate(steps, 1):
                        clean = step.strip()
                        if clean:
                            clean_clean = clean
                            import re
                            clean_clean = re.sub(r'^\d+\.\s*', '', clean)
                            lines.append(f"  {j}. {clean_clean}")
                    lines.append("")

                expected = s.get("expected_result", "")
                if expected:
                    lines.append(f"**Expected Result:** {expected}\n")

                success_criteria = s.get("success_criteria", [])
                if success_criteria:
                    lines.append("**Success Criteria:**\n")
                    for c in success_criteria:
                        lines.append(f"- {c}")
                    lines.append("")

                failure_conditions = s.get("failure_conditions", [])
                if failure_conditions:
                    lines.append("**Failure Conditions:**\n")
                    for c in failure_conditions:
                        lines.append(f"- {c}")
                    lines.append("")

                scenario_tags = s.get("tags", [])
                if scenario_tags:
                    lines.append("**Tags:** " + ", ".join(scenario_tags) + "\n")

                lines.append("---\n")

        coverage = plan.get("coverage_summary", "")
        if coverage:
            lines.append(f"## Coverage Summary\n\n{coverage}\n")

        assumptions = plan.get("assumptions", [])
        if assumptions:
            lines.append("## Assumptions\n")
            for a in assumptions:
                lines.append(f"- {a}")
            lines.append("")

        risks = plan.get("risks", [])
        if risks:
            lines.append("## Risks\n")
            for r in risks:
                lines.append(f"- {r}")
            lines.append("")

        lines.append("---\n*Generated by AI QA Platform*")
        return "\n".join(lines)

    @staticmethod
    def _parse_locator(primary):
        primary = primary.strip()

        if primary.startswith("getByRole"):
            return f"this.page.{primary}"
        if primary.startswith("getByLabel"):
            return f"this.page.{primary}"
        if primary.startswith("getByPlaceholder"):
            return f"this.page.{primary}"
        if primary.startswith("getByText"):
            return f"this.page.{primary}"
        if primary.startswith("getByTestId"):
            return f"this.page.{primary}"
        if primary.startswith("getByAltText"):
            return f"this.page.{primary}"
        if primary.startswith("getByTitle"):
            return f"this.page.{primary}"
        if primary.startswith("locator(") or primary.startswith("locator ("):
            return f"this.page.{primary}"
        if primary.startswith("page."):
            return f"this.{primary}"
        if primary.startswith("this."):
            return primary

        escaped = primary.replace("'", "\\'")
        return f"this.page.locator('{escaped}')"

    def update_registry(self, scenarios, test_file_path, url, feature_name):
        registry_path = os.path.join(self.output_dir, "tests", "test_registry.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)

        entries = []
        if os.path.isfile(registry_path):
            try:
                with open(registry_path, "r") as f:
                    entries = json.load(f)
            except Exception:
                entries = []

        for s in scenarios:
            entries.append({
                "id": str(uuid.uuid4()),
                "name": s.get("name", ""),
                "steps": s.get("steps", ""),
                "expected_result": s.get("expected_result", ""),
                "test_file": test_file_path,
                "url": url or "",
                "feature_name": feature_name or "app",
                "created_at": datetime.now().isoformat(),
            })

        with open(registry_path, "w") as f:
            json.dump(entries, f, indent=2)

    def write_report(self, execution_result, feature_name):
        reports_dir = os.path.join(self.output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        fname = f"{feature_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fpath = os.path.join(reports_dir, fname)

        status = execution_result.get("status", "unknown")
        passed = execution_result.get("passed", 0)
        failed = execution_result.get("failed", 0)
        skipped = execution_result.get("skipped", 0)
        logs = execution_result.get("logs", "")
        message = execution_result.get("message", "")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Test Report - {feature_name}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f1f5f9; margin: 0; padding: 24px; }}
    h1 {{ color: #6366f1; }}
    .status {{ padding: 12px 16px; border-radius: 8px; font-weight: 600; margin: 16px 0; }}
    .success {{ background: #166534; color: #22c55e; }}
    .failure {{ background: #7f1d1d; color: #ef4444; }}
    .error {{ background: #7f1d1d; color: #ef4444; }}
    .stats {{ display: flex; gap: 16px; margin: 16px 0; }}
    .stat {{ background: #1e293b; padding: 12px 20px; border-radius: 8px; }}
    .stat-value {{ font-size: 24px; font-weight: 700; }}
    pre {{ background: #1e293b; padding: 16px; border-radius: 8px; overflow-x: auto; max-height: 400px; }}
  </style>
</head>
<body>
  <h1>Test Report: {feature_name}</h1>
  <div class="status {status}">{status.upper()}</div>
  <p>{message}</p>
  <div class="stats">
    <div class="stat"><div class="stat-value" style="color:#22c55e">{passed}</div>Passed</div>
    <div class="stat"><div class="stat-value" style="color:#ef4444">{failed}</div>Failed</div>
    <div class="stat"><div class="stat-value" style="color:#94a3b8">{skipped}</div>Skipped</div>
  </div>
  <h2>Execution Logs</h2>
  <pre>{logs}</pre>
</body>
</html>"""
        with open(fpath, "w") as f:
            f.write(html)
        return fpath
