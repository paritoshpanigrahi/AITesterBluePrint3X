import json
import os
import uuid
from datetime import datetime


class TestRegistry:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def _get_registry_path(self):
        tests_dir = os.path.join(self.output_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        return os.path.join(tests_dir, "test_registry.json")

    def get_all(self):
        path = self._get_registry_path()
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def save_all(self, entries):
        path = self._get_registry_path()
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)

    def add_entry(self, entry):
        entries = self.get_all()
        entries.append(entry)
        self.save_all(entries)

    def delete(self, entry_id):
        entries = self.get_all()
        filtered = [e for e in entries if e.get("id") != entry_id]
        if len(filtered) == len(entries):
            return False
        self.save_all(filtered)
        return True
