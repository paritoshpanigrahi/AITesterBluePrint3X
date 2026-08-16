const BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8765').replace(/\/+$/, '');

async function apiRequest(path, options = {}) {
  const url = `${BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(url, config);
  if (!response.ok) {
    const err = await response.text().catch(() => '');
    throw new Error(`API Error ${response.status}: ${err || response.statusText}`);
  }
  return response.json();
}

export async function getHealth() {
  return apiRequest('/health');
}

export async function getConfig() {
  return apiRequest('/config');
}

export async function updateConfig(outputDir) {
  return apiRequest('/config', { method: 'POST', body: { output_dir: outputDir } });
}

export async function ingestContext(data) {
  return apiRequest('/ingest-context', { method: 'POST', body: data });
}

export async function generateTests(data) {
  return apiRequest('/generate-tests', { method: 'POST', body: data });
}

export async function addFeature(data) {
  return apiRequest('/add-feature', { method: 'POST', body: data });
}

export async function modifyTests(data) {
  return apiRequest('/modify-tests', { method: 'POST', body: data });
}

export async function getTestStructure(file) {
  return apiRequest(`/test-structure?file=${encodeURIComponent(file)}`);
}

export async function previewPlan(data) {
  return apiRequest('/preview-plan', { method: 'POST', body: data });
}

export async function runTests(data) {
  return apiRequest('/run-tests', { method: 'POST', body: data });
}

export async function createManualTests(data) {
  return apiRequest('/manual-tests', { method: 'POST', body: data });
}

export async function listManualTests() {
  return apiRequest('/manual-tests');
}

export async function getManualTest(slug) {
  return apiRequest(`/manual-tests/${slug}`);
}

export async function getRegistry() {
  return apiRequest('/registry');
}

export async function deleteRegistryEntry(id) {
  return apiRequest(`/registry/${id}`, { method: 'DELETE' });
}

export async function listReports() {
  return apiRequest('/reports');
}

export async function getReportUrl(filename) {
  return `${BASE}/reports/${filename}`;
}

export async function downloadReport(reportPath) {
  const filename = reportPath.split(/[\\/]/).pop();
  const response = await fetch(`${BASE}/reports/${encodeURIComponent(filename)}`);
  if (!response.ok) throw new Error('Failed to fetch report');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return apiRequest('/upload', { method: 'POST', body: formData, headers: {} });
}

export async function getModels() {
  return apiRequest('/models');
}

export async function testAtlassianCredentials() {
  return apiRequest('/test-atlassian-credentials', { method: 'POST' });
}

export async function exportTestPlan(testPlan, featureName, outputDir) {
  return apiRequest('/export-test-plan', {
    method: 'POST',
    body: { test_plan: testPlan, feature_name: featureName, output_dir: outputDir },
  });
}

export async function downloadPlan(filename) {
  const response = await fetch(`${BASE}/plans/${encodeURIComponent(filename)}`);
  if (!response.ok) throw new Error('Failed to fetch plan');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function browseDirectories(path = '') {
  const q = path ? `?path=${encodeURIComponent(path)}` : '';
  return apiRequest(`/browse-directories${q}`);
}

export async function checkSetup() {
  return apiRequest('/check-setup');
}

export async function setupPlaywright() {
  return apiRequest('/setup-playwright', { method: 'POST' });
}
