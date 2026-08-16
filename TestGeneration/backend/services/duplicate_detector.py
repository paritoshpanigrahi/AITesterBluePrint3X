import re
from difflib import SequenceMatcher


class DuplicateDetector:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.similarity_threshold = 0.85

    def check(self, scenarios, registry_entries):
        unique_scenarios = []
        duplicate_matches = []
        pending_actions = []

        for scenario in scenarios:
            name = scenario.get("name", "")
            steps = scenario.get("steps", "")
            is_dup = False
            best_match = None

            for entry in registry_entries:
                existing_name = entry.get("name", "")
                existing_steps = entry.get("steps", "")

                name_sim = SequenceMatcher(None, self._normalize(name), self._normalize(existing_name)).ratio()
                steps_sim = SequenceMatcher(None, self._normalize(steps), self._normalize(existing_steps)).ratio()

                if name_sim > self.similarity_threshold and steps_sim > self.similarity_threshold:
                    is_dup = True
                    best_match = {
                        "new_scenario_name": name,
                        "existing_id": entry.get("id", ""),
                        "existing_name": existing_name,
                        "existing_feature": entry.get("feature_name", ""),
                        "existing_test_file": entry.get("test_file", ""),
                        "name_similarity": round(name_sim, 3),
                        "steps_similarity": round(steps_sim, 3),
                    }
                    break

            if is_dup and best_match:
                duplicate_matches.append(best_match)
                pending_actions.append({
                    "scenario_name": name,
                    "existing_name": best_match["existing_name"],
                    "existing_id": best_match["existing_id"],
                    "name_similarity": best_match["name_similarity"],
                    "steps_similarity": best_match["steps_similarity"],
                    "action": "skip",
                    "options": ["skip", "override", "remove"],
                })
            else:
                unique_scenarios.append(scenario)

        return {
            "has_duplicates": len(duplicate_matches) > 0,
            "unique_scenarios": unique_scenarios,
            "duplicate_matches": duplicate_matches,
            "pending_actions": pending_actions,
        }

    def filter_unique(self, scenarios, registry_entries):
        result = self.check(scenarios, registry_entries)
        return result["unique_scenarios"]

    def resolve_actions(self, scenarios, registry_entries, scenario_actions):
        if not scenario_actions:
            return {"to_add": scenarios, "to_remove": [], "to_override": []}

        action_map = {}
        for sa in scenario_actions:
            action_map[sa.get("name", "")] = sa.get("action", "add")

        to_add = []
        to_remove = []
        to_override = []

        for scenario in scenarios:
            name = scenario.get("name", "")
            action = action_map.get(name, "add")
            if action == "add":
                to_add.append(scenario)
            elif action == "override":
                to_override.append(scenario)
            elif action == "skip":
                pass

        for entry in registry_entries:
            entry_name = entry.get("name", "")
            for sa in scenario_actions:
                if sa.get("existing_name") == entry_name and sa.get("action") == "remove":
                    to_remove.append(entry)
                elif sa.get("existing_name") == entry_name and sa.get("action") == "override":
                    to_remove.append(entry)

        return {
            "to_add": to_add,
            "to_remove": to_remove,
            "to_override": to_override,
        }

    def _normalize(self, text):
        if isinstance(text, list):
            text = "\n".join(str(s) for s in text)
        text = (text or "").lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
