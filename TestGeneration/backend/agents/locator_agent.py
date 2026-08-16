import json
import os
import re
from backend.utils.skill_loader import load_skill
from backend.agents._client_factory import call_llm
from backend.services.crawler import Crawler
from backend.ingestion.codebase_analyzer import CodebaseAnalyzer


class LocatorAgent:
    def __init__(self):
        self.skill = load_skill("locator_agent")
        self.analyzer = CodebaseAnalyzer()

    async def generate(self, url, codebase_path=None, codebase_context=None):
        url_locators = {}
        codebase_locators = {}
        page_locators = {}

        if url:
            crawler = Crawler()
            dom_snapshot = await crawler.crawl(url)
            if self._is_valid_dom(dom_snapshot):
                url_locators = await self._generate_from_dom(url, dom_snapshot)

            if not url_locators:
                try:
                    pw_dom = await crawler.crawl_with_playwright(url)
                    if self._is_valid_dom(pw_dom):
                        url_locators = await self._generate_from_dom(url, pw_dom)
                except Exception:
                    pass

            if url_locators:
                page_name = self._page_name_from_url(url)
                page_locators[page_name] = url_locators

        if codebase_path and os.path.isdir(codebase_path):
            codebase_locators = await self.generate_from_codebase(codebase_path, codebase_context)

        if not codebase_locators and codebase_context and isinstance(codebase_context, dict) and codebase_context.get("components"):
            codebase_locators = self._fallback_from_analysis(codebase_context)

        # Crawl all discovered routes from codebase analysis for more accurate locators
        url_page_has_login = any(x in str(url_locators).lower() for x in ["username", "password", "signin", "sign_in"])
        if url and codebase_context and isinstance(codebase_context, dict):
            routes = codebase_context.get("routes", [])
            unique_routes = list(dict.fromkeys(
                r for r in routes
                if isinstance(r, str) and r.startswith('/') and '{' not in r and ':' not in r
            ))
            if unique_routes:
                base_url = self._extract_base_url(url)
                crawler = Crawler()
                auth_config = {
                    "login_url": "/login",
                    "username": "admin",
                    "password": "admin123",
                    "username_selector": "#username",
                    "password_selector": "#password",
                    "submit_selector": "button[type='submit']",
                }
                route_doms = await crawler.crawl_multiple(base_url, unique_routes, auth=auth_config)
                for route, elements_str in route_doms.items():
                    if elements_str and len(elements_str) > 100:
                        route_url = base_url.rstrip('/') + route
                        locators = await self._generate_from_dom(route_url, elements_str)
                        if locators:
                            # Skip if route crawl returned login page (auth redirect)
                            if url_page_has_login and route != '/login':
                                has_login_els = any(x in str(locators).lower() for x in ["username", "password", "signin", "sign_in"])
                                if has_login_els:
                                    continue
                            page_name = self._page_name_from_route(route)
                            if page_name in page_locators:
                                page_locators[page_name].update(locators)
                            else:
                                page_locators[page_name] = locators

        # Merge all page locators into flat dict
        merged = dict(codebase_locators) if codebase_locators else {}
        for page_locs in page_locators.values():
            merged.update(page_locs)
        if not merged:
            merged = codebase_locators or {}
        if not merged and url_locators:
            merged = url_locators

        if "app" in page_locators:
            del page_locators["app"]

        # Build per-page locators by matching route keywords to element source files
        if merged and codebase_context and isinstance(codebase_context, dict):
            all_els = codebase_context.get("all_elements", []) or []
            routes = codebase_context.get("routes", [])
            unique_routes = list(dict.fromkeys(
                r for r in routes
                if isinstance(r, str) and r.startswith('/') and '{' not in r and ':' not in r
            ))
            if all_els and unique_routes:
                url_page_name = self._page_name_from_url(url) if url else None
                layout_keywords = ["layout", "navbar", "nav", "sidebar", "main", "app"]
                layout_keys = set()
                for loc_key in merged:
                    lk = loc_key.lower()
                    if any(x in lk for x in ["navlink", "logout", "gotodashboard"]):
                        layout_keys.add(loc_key)

                for route in sorted(unique_routes):
                    pn = self._page_name_from_route(route)
                    if pn in page_locators:
                        continue
                    # Build a set of source filenames that could be this page
                    page_src_variants = {pn, pn.capitalize(), pn.title(), pn.upper()}
                    loc_keys_for_route = set()
                    for el in all_els:
                        src = os.path.splitext(os.path.basename(el.get("file", "")))[0]
                        if not src:
                            continue
                        src_lower = src.lower()
                        if any(kw in src_lower for kw in layout_keywords):
                            continue
                        # Check if source filename matches the page name
                        if src.lower() != pn.lower():
                            continue
                        for key in self._infer_key_from_element(el):
                            if key in merged:
                                loc_keys_for_route.add(key)
                    if loc_keys_for_route:
                        locs = {k: merged[k] for k in (loc_keys_for_route | layout_keys) if k in merged}
                        if locs:
                            page_locators[pn] = locs

        return merged, page_locators

    @staticmethod
    def _infer_key_from_element(el):
        """Given a codebase element dict, return candidate locator key names.
        Mirrors the key generation logic in _fallback_from_elements."""
        keys = set()
        el_type = el.get("type", "")
        el_id = el.get("id", "")
        text = el.get("text", "")
        placeholder = el.get("placeholder", "")
        class_name = el.get("className", "")
        aria_label = el.get("aria_label", "")

        if el_type == "input":
            if el_id:
                keys.add(f"{el_id}Input")
            if placeholder:
                s = LocatorAgent._sanitize_name(placeholder.split("...")[0].strip())
                if s:
                    keys.add(f"{s}Input")

        elif el_type == "button":
            if text:
                s = LocatorAgent._sanitize_name(text)
                if s:
                    keys.add(f"{s}_button")
                # qa- class buttons get key without qa- prefix
                if class_name and "qa-" in class_name:
                    cls_parts = class_name.split()
                    unique_qa = [p for p in cls_parts if "qa-" in p and p != "qa-btn"]
                    if unique_qa:
                        keys.add(unique_qa[0].replace("qa-", "") + "_button")
                    else:
                        keys.add(cls_parts[-1] + "_button")
            elif aria_label:
                s = LocatorAgent._sanitize_name(aria_label)
                if s:
                    keys.add(f"{s}_button")

        elif el_type == "select":
            opts = el.get("options", [])
            if opts:
                s = LocatorAgent._sanitize_name(opts[0])
                if s:
                    keys.add(f"{s}Select")
            if class_name and "filter" in class_name.lower():
                keys.add("filterSelect")

        elif el_type == "textarea":
            if placeholder:
                s = LocatorAgent._sanitize_name(placeholder)
                if s:
                    keys.add(f"{s}Textarea")

        elif el_type == "link":
            link_text = el.get("text", "")
            link_to = el.get("to", "")
            if link_to and ("{" in link_text or len(link_text) > 50):
                s = LocatorAgent._sanitize_name(link_to.replace("/", " ").strip() or "link")
                if s:
                    keys.add(f"{s}NavLink")
            elif link_text:
                s = LocatorAgent._sanitize_name(link_text)
                if s:
                    keys.add(f"{s}Link")
                if link_to:
                    ls = LocatorAgent._sanitize_name(link_to.replace("/", " ").strip() or "link")
                    if ls:
                        keys.add(f"{ls}NavLink")

        return keys

    @staticmethod
    def _page_name_from_url(url):
        try:
            from urllib.parse import urlparse
            path = urlparse(url).path.rstrip('/')
            if not path or path == '/':
                return "home"
            return path.strip('/').split('/')[-1]
        except Exception:
            return "app"

    @staticmethod
    def _page_name_from_route(route):
        name = route.strip('/').replace('/', '_') if route else ""
        return name or "home"

    @staticmethod
    def _extract_base_url(url):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return url

    def _is_valid_dom(self, dom):
        return dom and len(dom) > 100 and not dom.startswith("Failed") and not dom.startswith("Error")

    async def _generate_from_dom(self, url, dom_snapshot):
        system_prompt = self.skill
        user_prompt = f"""
URL: {url}

DOM elements:
{dom_snapshot[:8000]}

Generate Playwright locators for all interactive elements.
Preferred strategies (in order): getByRole, getByPlaceholder, getByText, getByLabel, #id, button:has-text("text"), a:has-text("text"), .class.
Return a JSON object where keys are camelCase element names and values have "primary" and "fallbacks" fields.
"""
        try:
            content = await call_llm(system_prompt, user_prompt, max_tokens=4096)
            return self._extract_json(content)
        except Exception as e:
            import traceback
            import sys
            print(f"[LOCATOR WARN] _generate_from_dom failed for {url}: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {}

    def _extract_json(self, text):
        import re
        text = text.strip()
        idx = text.find('{')
        if idx == -1:
            return {}
        text = text[idx:]
        depth = 0
        for i, ch in enumerate(text):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[:i+1])
                    except json.JSONDecodeError:
                        return {}
        return {}

    async def generate_from_codebase(self, codebase_path, codebase_context=None):
        analysis = self.analyzer.analyze(codebase_path)
        if not analysis.get("components") and not analysis.get("routes") and not analysis.get("all_elements"):
            return {}

        llm_result = await self._generate_from_analysis_with_llm(analysis)
        if llm_result:
            return llm_result

        return self._fallback_from_analysis(analysis)

    async def _generate_from_analysis_with_llm(self, analysis):
        elements_summary = self._build_elements_summary(analysis)
        if not elements_summary:
            return None

        routes = analysis.get("routes", [])
        routes_str = "\n".join(f"  - {r}" for r in routes[:20]) if routes else "  (none detected)"

        system_prompt = self.skill
        user_prompt = f"""
Codebase Analysis Summary:

Routes:
{routes_str}

Interactive Elements Found:
{elements_summary}

Generate stable Playwright locators for ALL interactive elements across all pages.
For each element, use the BEST selector strategy:
1. `getByRole('button', {{ name: /Text/i }})` for buttons with text
2. `getByLabel('Label Text')` for inputs with associated labels
3. `getByPlaceholder('placeholder text')` for inputs with placeholders
4. `page.locator('#id')` for elements with stable IDs
5. `page.locator('button:has-text("Text")')` for buttons as fallback
6. `page.locator('[placeholder="text"]')` for inputs as fallback
7. `page.getByRole('combobox', {{ name: /label/i }})` for select elements
8. `page.locator('.className')` only as last resort

Return a JSON object where keys are camelCase element names (like "usernameInput", "signInButton")
and values have "primary" and "fallbacks" fields with valid Playwright selectors.
IMPORTANT: Do NOT use HTML entities like &times; in locators. Decode them to actual characters.
"""
        try:
            content = await call_llm(system_prompt, user_prompt, max_tokens=4096)
            result = self._extract_json(content)
            if isinstance(result, dict) and len(result) > 0:
                return result
            return None
        except Exception:
            return None

    def _build_elements_summary(self, analysis):
        lines = []
        pages = {}

        for el in analysis.get("all_elements", []):
            fname = el.get("file", "unknown")
            page_name = fname.replace(".jsx", "").replace(".tsx", "").replace(".js", "").replace(".ts", "")
            if page_name not in pages:
                pages[page_name] = []
            el_type = el.get("type", "")
            if el_type == "input":
                desc = f"  Input: type={el.get('input_type', 'text')}, placeholder='{el.get('placeholder', '')}', id='{el.get('id', '')}'"
            elif el_type == "button":
                desc = f"  Button: text='{el.get('text', '')}', className='{el.get('className', '')}'"
            elif el_type == "select":
                desc = f"  Select: className='{el.get('className', '')}', options={el.get('options', [])}"
            elif el_type == "textarea":
                desc = f"  Textarea: placeholder='{el.get('placeholder', '')}'"
            elif el_type == "link":
                link_to = el.get('to', '')
                link_text = el.get('text', '')
                if len(link_text) > 60:
                    link_text = link_text[:60] + "..."
                desc = f"  Link: text='{link_text}', to='{link_to}'"
            elif el_type == "checkbox":
                desc = f"  Checkbox: className='{el.get('className', '')}'"
            else:
                continue
            pages[page_name].append(desc)

        for page_name, elements in pages.items():
            lines.append(f"\n[{page_name}]")
            for el in elements:
                lines.append(el)

        return "\n".join(lines)

    @staticmethod
    def _sanitize_name(raw):
        s = raw.replace("&", "").replace("#", "").replace(";", "")
        s = re.sub(r'[^a-zA-Z0-9\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        words = [w for w in s.split() if w and not w[0].isdigit()]
        if not words:
            words = [w for w in s.split() if w]
        if not words:
            return ""
        result = "".join(w.capitalize() for w in words)
        result = result[0].lower() + result[1:]
        if result and result[0].isdigit():
            result = "_" + result
        return result

    @staticmethod
    def _decode_entities(text):
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        text = text.replace("&times;", "x")
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if 32 <= int(m.group(1)) <= 126 else 'x', text)
        return text

    def _fallback_from_analysis(self, analysis):
        locators = {}
        seen_primary = set()

        all_els = analysis.get("all_elements", [])
        if all_els:
            return self._fallback_from_elements(all_els)

        for fname, comp in analysis.get("components", {}).items():
            for inp in comp.get("inputs", []):
                if inp.get("id"):
                    name = f"{inp['id']}Input"
                    primary = f"#{inp['id']}"
                    if primary not in seen_primary:
                        locators[name] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        if inp.get("placeholder"):
                            locators[name]["fallbacks"].append(f"[placeholder=\"{inp['placeholder']}\"]")

            for label in comp.get("labels", []):
                for inp in comp.get("inputs", []):
                    if inp.get("id") == label.get("htmlFor"):
                        primary = f"#{inp['id']}"
                        if primary not in seen_primary:
                            label_name = self._sanitize_name(label["text"] + " Input")
                            if label_name and label_name not in locators:
                                locators[label_name] = {
                                    "primary": primary,
                                    "fallbacks": [f"label:text(\"{label['text']}\")/.. input"]
                                }
                                seen_primary.add(primary)

            for btn in comp.get("buttons", []):
                if btn.get("text"):
                    btn_text = self._decode_entities(btn["text"])
                    primary = f"button:has-text(\"{btn_text}\")"
                    if primary not in seen_primary:
                        key = self._sanitize_name(btn_text) + "_button"
                        if not key or key == "_button":
                            key = "submit_button"
                        has_non_ascii = any(ord(c) > 127 for c in btn_text)
                        if has_non_ascii and btn.get("className"):
                            primary = f".{btn['className'].replace(' ', '.')}"
                        locators[key] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        if btn.get("className"):
                            cls = btn["className"].replace(" ", ".")
                            if cls:
                                locators[key]["fallbacks"].append(f".{cls}")

        for k, v in list(locators.items()):
            v["primary"] = v["primary"].encode("ascii", "ignore").decode("ascii")
            v["fallbacks"] = [f.encode("ascii", "ignore").decode("ascii") for f in v.get("fallbacks", [])]
        return locators

    def _fallback_from_elements(self, all_elements):
        locators = {}
        seen_primary = set()
        combobox_count = 0
        seen_buttons = {}  # text -> counter to disambiguate

        for el in all_elements:
            el_type = el.get("type", "")

            if el_type == "input":
                el_id = el.get("id", "")
                placeholder = el.get("placeholder", "")
                input_type = el.get("input_type", "text")
                if el_id:
                    name = f"{el_id}Input"
                    primary = f"#{el_id}"
                    if primary not in seen_primary:
                        locators[name] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        if placeholder:
                            locators[name]["fallbacks"].append(f"getByPlaceholder('{placeholder}')")
                elif placeholder:
                    sanitized = self._sanitize_name(placeholder.split("...")[0].strip())
                    name = f"{sanitized}Input" if sanitized else f"{input_type}Input"
                    primary = f"getByPlaceholder('{placeholder}')"
                    if primary not in seen_primary:
                        locators[name] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        locators[name]["fallbacks"].append(f"input[type=\"{input_type}\"]")

            elif el_type == "button":
                btn_text = el.get("text", "")
                had_entities = el.get("had_entities", False)
                aria_label = el.get("aria_label", "")
                class_name = el.get("className", "")
                if btn_text:
                    if btn_text in seen_buttons:
                        seen_buttons[btn_text] += 1
                        suffix = str(seen_buttons[btn_text])
                    else:
                        seen_buttons[btn_text] = 1
                        suffix = ""
                    key = self._sanitize_name(btn_text) + "_button" + suffix
                    if not key.replace("_button", "") or key == "_button":
                        key = "submit_button" + suffix
                    if class_name and (had_entities or len(btn_text) < 2):
                        name_key = self._sanitize_name(btn_text)
                        key = f"{name_key}_button" if name_key else "icon_button"
                        if "qa-" in class_name:
                            cls_parts = class_name.split()
                            unique_qa = [p for p in cls_parts if "qa-" in p and p != "qa-btn"]
                            if unique_qa:
                                qa_class = unique_qa[0]
                            else:
                                qa_class = cls_parts[-1]
                            key = qa_class.replace("qa-", "") + "_button"
                        primary = f".{class_name.replace(' ', '.')}"
                    else:
                        primary = f"getByRole('button', {{ name: /{re.escape(btn_text)}/i }})"
                    if primary not in seen_primary:
                        locators[key] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        if not class_name or not had_entities:
                            locators[key]["fallbacks"].append(f"button:has-text(\"{btn_text}\")")
                        if class_name and primary != f".{class_name.replace(' ', '.')}":
                            cls = class_name.replace(" ", ".")
                            locators[key]["fallbacks"].append(f".{cls}")
                elif aria_label:
                    primary = f"getByRole('button', {{ name: /{re.escape(aria_label)}/i }})"
                    if primary not in seen_primary:
                        key = self._sanitize_name(aria_label) + "_button"
                        locators[key] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        if class_name:
                            cls = class_name.replace(" ", ".")
                            locators[key]["fallbacks"].append(f".{cls}")

            elif el_type == "select":
                class_name = el.get("className", "")
                options = el.get("options", [])
                option_hint = options[0] if options else "select"
                sanitized = self._sanitize_name(option_hint)
                name = f"{sanitized}Select" if sanitized else "filterSelect"
                if class_name:
                    primary = f".{class_name.replace(' ', '.')}"
                    name = f"{sanitized}Select" if sanitized else "filterSelect"
                else:
                    combobox_count += 1
                    primary = f"getByRole('combobox')"
                    if combobox_count > 1:
                        name = f"filterSelect_{combobox_count}"
                if primary not in seen_primary:
                    locators[name] = {"primary": primary, "fallbacks": []}
                    seen_primary.add(primary)

            elif el_type == "textarea":
                placeholder = el.get("placeholder", "")
                if placeholder:
                    sanitized = self._sanitize_name(placeholder)
                    name = f"{sanitized}Textarea" if sanitized else "descriptionTextarea"
                    primary = f"getByPlaceholder('{placeholder}')"
                    if primary not in seen_primary:
                        locators[name] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)

            elif el_type == "link":
                raw_text = el.get("text", "")
                link_text = self._decode_entities(raw_text)
                link_to = el.get("to", "")
                class_name = el.get("className", "")
                if "{" in raw_text or "&#" in raw_text or len(raw_text) > 50:
                    if link_to:
                        name = self._sanitize_name(link_to.replace("/", " ").strip() or "link")
                        name = f"{name}NavLink" if name else "navLink"
                        primary = f"a[href=\"{link_to}\"]"
                        if primary not in seen_primary:
                            locators[name] = {"primary": primary, "fallbacks": []}
                            seen_primary.add(primary)
                            if class_name:
                                cls = class_name.replace(" ", ".")
                                locators[name]["fallbacks"].append(f".{cls}")
                elif link_text:
                    primary = f"getByRole('link', {{ name: /{re.escape(link_text)}/i }})"
                    if primary not in seen_primary:
                        sanitized = self._sanitize_name(link_text)
                        name = f"{sanitized}Link" if sanitized else f"linkTo_{link_to.replace('/', '_')}"
                        locators[name] = {"primary": primary, "fallbacks": []}
                        seen_primary.add(primary)
                        locators[name]["fallbacks"].append(f"a:has-text(\"{link_text}\")")
                        if link_to:
                            locators[name]["fallbacks"].append(f"a[href=\"{link_to}\"]")

        return locators

    async def generate_from_hints(self, url, element_hints):
        if not url:
            return {}

        hints_text = "\n".join([f"- {h.name}: tag={h.tag}, id={h.id}, testid={h.data_testid}" for h in element_hints if h.name])

        system_prompt = self.skill
        user_prompt = f"""
URL: {url}

Element Hints:
{hints_text}

Generate stable Playwright locators for these elements.
Return a JSON object where keys are element names and values have "primary" and "fallbacks" fields.
"""
        try:
            content = await call_llm(system_prompt, user_prompt)
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception:
            return {}
