import os
import json
import re
from pathlib import Path


class CodebaseAnalyzer:
    def analyze(self, codebase_path):
        result = {
            "routes": [],
            "component_map": {},
            "element_hints": [],
            "api_endpoints": [],
            "inferred_base_url": None,
            "framework": None,
            "components": {},
            "all_elements": [],
            "modals": [],
            "route_to_component": {},
        }

        if not codebase_path or not os.path.isdir(codebase_path):
            return result

        codebase_path = str(codebase_path)

        for root, dirs, files in os.walk(codebase_path):
            if "node_modules" in root or ".git" in root or "__pycache__" in root:
                continue

            for fname in files:
                if fname.endswith((".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        self._analyze_file(fpath, content, result)
                    except Exception:
                        pass

        return result

    def _analyze_file(self, fpath, content, result):
        name = os.path.basename(fpath)
        result["component_map"][name] = fpath

        routes = re.findall(r'(?:path|route|to)=["\']([^"\']+)["\']', content)
        result["routes"].extend(routes)
        for r in routes:
            result["route_to_component"][r] = name

        apis = re.findall(r'(?:fetch|axios|api|axiosInstance)\s*\(\s*["\']https?://[^"\']+["\']', content)
        apis2 = re.findall(r'(?:fetch|axios|api)\(["\'](/[^"\']+)["\']', content)
        result["api_endpoints"].extend(apis)
        result["api_endpoints"].extend(apis2)

        element_hints = re.findall(r'(?:data-testid|data-test|testId)=["\']([^"\']+)["\']', content)
        for hint in element_hints:
            result["element_hints"].append({"name": hint, "data_testid": hint})

        lower = content.lower()
        if "react" in lower:
            result["framework"] = "react"
        elif "vue" in lower:
            result["framework"] = "vue"
        elif "angular" in lower:
            result["framework"] = "angular"

        component_info = self._extract_form_elements(content, name)
        if component_info:
            result["components"][name] = component_info

        elements = self._extract_all_interactive_elements(content, name)
        if elements:
            result["all_elements"].extend(elements)

        modals = self._extract_modals(content, name)
        if modals:
            result["modals"].extend(modals)

    def _extract_all_interactive_elements(self, content, filename):
        elements = []

        input_pattern = re.compile(r'<input\s([^>]*?)(?:/?)>', re.IGNORECASE)
        for match in input_pattern.finditer(content):
            attrs_str = match.group(1)
            attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', attrs_str))
            elements.append({
                "type": "input",
                "id": attrs.get("id", ""),
                "input_type": attrs.get("type", "text"),
                "placeholder": attrs.get("placeholder", ""),
                "name": attrs.get("name", ""),
                "className": attrs.get("className", ""),
                "autoFocus": "autofocus" in attrs_str.lower() or "autoFocus" in attrs,
                "file": filename,
            })

        button_pattern = re.compile(r'<button((?:\s+[\w-]+(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'|\{[^}]*\}))?)*)\s*>(.*?)</button>', re.IGNORECASE | re.DOTALL)
        for match in button_pattern.finditer(content):
            btn_attrs = dict(re.findall(r'([\w-]+)=["\']([^"\']*)["\']', match.group(1)))
            btn_inner = match.group(2)
            btn_inner_raw = btn_inner
            btn_inner_stripped = re.sub(r'\{[^}]*\}', '', btn_inner)
            btn_inner_stripped = re.sub(r'<[^>]+>', '', btn_inner_stripped)
            had_entities = "&#" in btn_inner_stripped
            btn_inner_stripped = self._decode_entities(btn_inner_stripped)
            btn_inner_stripped = re.sub(r'\s+', ' ', btn_inner_stripped)
            btn_text = btn_inner_stripped.strip()
            if btn_text or btn_attrs.get("aria-label"):
                elements.append({
                    "type": "button",
                    "text": btn_text[:100] if btn_text else "",
                    "had_entities": had_entities,
                    "aria_label": btn_attrs.get("aria-label", ""),
                    "className": btn_attrs.get("className", ""),
                    "button_type": btn_attrs.get("type", ""),
                    "file": filename,
                })

        select_pattern = re.compile(r'<select\s([^>]*?)>(.*?)</select>', re.IGNORECASE | re.DOTALL)
        for match in select_pattern.finditer(content):
            select_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', match.group(1)))
            options = re.findall(r'<option[^>]*?>(.*?)</option>', match.group(2))
            option_texts = []
            for opt in options:
                opt_clean = re.sub(r'<[^>]+>', '', opt).strip()
                if opt_clean:
                    option_texts.append(opt_clean[:40])
            elements.append({
                "type": "select",
                "className": select_attrs.get("className", ""),
                "id": select_attrs.get("id", ""),
                "options": option_texts[:10],
                "file": filename,
            })

        textarea_pattern = re.compile(r'<textarea\s([^>]*?)>(.*?)</textarea>', re.IGNORECASE | re.DOTALL)
        for match in textarea_pattern.finditer(content):
            ta_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', match.group(1)))
            elements.append({
                "type": "textarea",
                "id": ta_attrs.get("id", ""),
                "placeholder": ta_attrs.get("placeholder", ""),
                "className": ta_attrs.get("className", ""),
                "rows": ta_attrs.get("rows", ""),
                "file": filename,
            })

        link_pattern = re.compile(r'<(?:NavLink|Link|a)\s([^>]*?)>(.*?)</(?:NavLink|Link|a)>', re.IGNORECASE | re.DOTALL)
        for match in link_pattern.finditer(content):
            link_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', match.group(1)))
            link_text = re.sub(r'<[^>]+>', "", match.group(2)).strip()
            link_to = link_attrs.get("to", link_attrs.get("href", ""))
            if link_text or link_to:
                elements.append({
                    "type": "link",
                    "text": link_text[:80],
                    "to": link_to,
                    "className": link_attrs.get("className", ""),
                    "file": filename,
                })

        checkbox_pattern = re.compile(r'<input\s[^>]*?type=["\']checkbox["\'][^>]*?>', re.IGNORECASE)
        for match in checkbox_pattern.finditer(content):
            attrs_str = match.group(0)
            cb_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', attrs_str))
            elements.append({
                "type": "checkbox",
                "id": cb_attrs.get("id", ""),
                "className": cb_attrs.get("className", ""),
                "file": filename,
            })

        return elements

    def _extract_modals(self, content, filename):
        modals = []
        modal_pattern = re.compile(r'className=["\'][^"\']*modal[^"\']*["\']', re.IGNORECASE)
        if modal_pattern.search(content):
            modal_info = {"file": filename, "source_preview": content[:2000]}
            modals.append(modal_info)
        return modals

    def _extract_form_elements(self, content, filename):
        info = {"inputs": [], "buttons": [], "labels": [], "forms": [], "links": []}

        input_pattern = re.compile(r'<input\s([^>]*?)(?:/?)>', re.IGNORECASE)
        for match in input_pattern.finditer(content):
            attrs_str = match.group(1)
            attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', attrs_str))
            if attrs.get("id") or attrs.get("name") or attrs.get("placeholder") or attrs.get("type"):
                info["inputs"].append({
                    "id": attrs.get("id", ""),
                    "type": attrs.get("type", "text"),
                    "placeholder": attrs.get("placeholder", ""),
                    "name": attrs.get("name", ""),
                    "className": attrs.get("className", ""),
                })

        button_pattern = re.compile(r'<button((?:\s+[\w-]+(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'|\{[^}]*\}))?)*)\s*>(.*?)</button>', re.IGNORECASE | re.DOTALL)
        for match in button_pattern.finditer(content):
            btn_attrs = dict(re.findall(r'([\w-]+)=["\']([^"\']*)["\']', match.group(1)))
            btn_inner = match.group(2)
            btn_inner = re.sub(r'\{[^}]*\}', '', btn_inner)
            btn_inner = re.sub(r'<[^>]+>', '', btn_inner)
            btn_inner = self._decode_entities(btn_inner)
            btn_inner = re.sub(r'\s+', ' ', btn_inner)
            btn_text = btn_inner.strip()
            if btn_text:
                info["buttons"].append({
                    "text": btn_text[:80],
                    "className": btn_attrs.get("className", ""),
                    "type": btn_attrs.get("type", ""),
                })

        label_pattern = re.compile(r'<label[^>]*?htmlFor=["\']([^"\']+)["\'][^>]*?>(.*?)</label>', re.IGNORECASE | re.DOTALL)
        for match in label_pattern.finditer(content):
            label_text = re.sub(r'<[^>]+>', "", match.group(2)).strip()
            info["labels"].append({
                "htmlFor": match.group(1),
                "text": label_text[:80],
            })

        # Also find plain text labels (no htmlFor) that precede inputs
        plain_label_pattern = re.compile(r'<label[^>]*?>(.*?)</label>', re.IGNORECASE | re.DOTALL)
        for match in plain_label_pattern.finditer(content):
            label_html = match.group(0)
            if 'htmlFor' not in label_html:
                label_text = re.sub(r'<[^>]+>', "", match.group(1)).strip()
                if label_text:
                    info["labels"].append({
                        "htmlFor": "",
                        "text": label_text[:80],
                    })

        form_pattern = re.compile(r'<form\s([^>]*?)>', re.IGNORECASE)
        for match in form_pattern.finditer(content):
            form_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', match.group(1)))
            info["forms"].append({
                "className": form_attrs.get("className", ""),
                "id": form_attrs.get("id", ""),
                "name": form_attrs.get("name", ""),
                "onSubmit": form_attrs.get("onSubmit", ""),
            })

        link_pattern = re.compile(r'<(?:NavLink|Link|a)\s([^>]*?)>(.*?)</(?:NavLink|Link|a)>', re.IGNORECASE | re.DOTALL)
        for match in link_pattern.finditer(content):
            link_attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', match.group(1)))
            link_text = re.sub(r'<[^>]+>', "", match.group(2)).strip()
            link_to = link_attrs.get("to", link_attrs.get("href", ""))
            if link_text or link_to:
                info["links"].append({
                    "to": link_to,
                    "text": link_text[:80],
                    "className": link_attrs.get("className", ""),
                })

        has_content = any(v for v in info.values())
        if has_content:
            preview = content[:3000]
            info["source_preview"] = preview
            info["file"] = filename
            return info

        return None

    @staticmethod
    def _decode_entities(text):
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        text = text.replace("&times;", "x")
        text = text.replace("&#10003;", "x")
        text = text.replace("&#9998;", "x")
        text = text.replace("&#9783;", "x")
        text = text.replace("&#9881;", "x")
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if 32 <= int(m.group(1)) <= 126 else 'x', text)
        return text

    def _find_base_url(self, content):
        match = re.search(r'baseURL\s*[:=]\s*["\'](https?://[^"\']+)["\']', content)
        if match:
            return match.group(1)
        match = re.search(r'BASE_URL\s*=\s*["\'](https?://[^"\']+)["\']', content)
        if match:
            return match.group(1)
        return None
