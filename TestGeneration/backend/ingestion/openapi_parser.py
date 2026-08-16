import json
import yaml


class OpenApiParser:
    def parse(self, filepath):
        if not filepath:
            return []

        try:
            with open(filepath, "r") as f:
                content = f.read()

            if filepath.endswith((".yaml", ".yml")):
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            endpoints = []
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    if isinstance(details, dict):
                        summary = details.get("summary", details.get("operationId", ""))
                        endpoints.append(f"{method.upper()} {path} - {summary}")
            return endpoints
        except Exception:
            return []
