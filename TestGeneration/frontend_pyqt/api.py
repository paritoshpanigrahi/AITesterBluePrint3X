import requests
import os

BASE_URL = "http://localhost:8765"

def get_health():
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    r.raise_for_status()
    return r.json()

def get_config():
    r = requests.get(f"{BASE_URL}/config", timeout=5)
    r.raise_for_status()
    return r.json()

def update_config(output_dir):
    r = requests.post(f"{BASE_URL}/config", json={"output_dir": output_dir}, timeout=5)
    r.raise_for_status()
    return r.json()

def ingest_context(payload):
    r = requests.post(f"{BASE_URL}/ingest-context", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def generate_tests(payload):
    r = requests.post(f"{BASE_URL}/generate-tests", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def add_feature(payload):
    r = requests.post(f"{BASE_URL}/add-feature", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def modify_tests(payload):
    r = requests.post(f"{BASE_URL}/modify-tests", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def preview_plan(payload):
    r = requests.post(f"{BASE_URL}/preview-plan", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def run_tests(payload):
    r = requests.post(f"{BASE_URL}/run-tests", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def get_test_structure(file_path):
    r = requests.get(f"{BASE_URL}/test-structure", params={"file": file_path}, timeout=30)
    r.raise_for_status()
    return r.json()

def get_registry():
    r = requests.get(f"{BASE_URL}/registry", timeout=30)
    r.raise_for_status()
    return r.json()

def delete_registry_entry(entry_id):
    r = requests.delete(f"{BASE_URL}/registry/{entry_id}", timeout=30)
    r.raise_for_status()
    return r.json()

def create_manual_tests(payload):
    r = requests.post(f"{BASE_URL}/manual-tests", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def list_manual_tests():
    r = requests.get(f"{BASE_URL}/manual-tests", timeout=30)
    r.raise_for_status()
    return r.json()

def get_manual_test(slug):
    r = requests.get(f"{BASE_URL}/manual-tests/{slug}", timeout=30)
    r.raise_for_status()
    return r.json()

def list_reports():
    r = requests.get(f"{BASE_URL}/reports", timeout=30)
    r.raise_for_status()
    return r.json()

def get_report(filename):
    r = requests.get(f"{BASE_URL}/reports/{filename}", timeout=30)
    r.raise_for_status()
    return r.json()

def download_report(filepath):
    r = requests.get(f"{BASE_URL}/reports/{os.path.basename(filepath)}", timeout=30)
    r.raise_for_status()
    return r.content

def upload_file(filepath):
    with open(filepath, "rb") as f:
        r = requests.post(f"{BASE_URL}/upload", files={"file": f}, timeout=120)
    r.raise_for_status()
    return r.json()

def test_atlassian_credentials():
    r = requests.post(f"{BASE_URL}/test-atlassian-credentials", timeout=30)
    r.raise_for_status()
    return r.json()

def get_models():
    r = requests.get(f"{BASE_URL}/models", timeout=30)
    r.raise_for_status()
    return r.json()

def export_test_plan(test_plan, feature_name="test-plan"):
    r = requests.post(f"{BASE_URL}/export-test-plan", json={"test_plan": test_plan, "feature_name": feature_name}, timeout=30)
    r.raise_for_status()
    return r.json()

def download_plan(filename, save_path):
    r = requests.get(f"{BASE_URL}/plans/{filename}", timeout=30)
    r.raise_for_status()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(r.content)
    return save_path
