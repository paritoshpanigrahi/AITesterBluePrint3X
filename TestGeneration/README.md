# AI QA Platform

> AI-powered test generation platform that automatically creates Playwright automation tests and structured manual test cases from a requirement, a URL, a codebase, PRD documents, Jira tickets, and Confluence pages.

---

## Project Title

**AI QA Platform** — an AI-driven software quality assurance tool that turns product requirements into ready-to-run automated tests and comprehensive manual test suites.

## Problem Statement

Writing and maintaining test cases is one of the most time-consuming and error-prone parts of software delivery:

- **Slow manual effort** — QA engineers manually translate requirements into test cases, one by one.
- **Incomplete coverage** — happy-path tests get written, while negative, edge-case, smoke, and regression scenarios are often missed.
- **Fragile automation** — Playwright tests break when the UI changes, and fixing selectors requires constant rework.
- **Knowledge silos** — useful context lives in PRDs, Jira tickets, Confluence pages, API specs, and source code, but is rarely used to drive test creation.
- **Duplicate tests** — different features and contributors produce overlapping scenarios that clutter the test suite.

## Solution

AI QA Platform is a multi-agent AI system that converts natural-language inputs into quality engineering artifacts. It:

1. **Ingests context** from multiple sources — raw requirement text, PRD/Word/PDF documents, a live application URL, a source-code repository, an OpenAPI spec, Jira tickets/sprints, and Confluence pages.
2. **Uses a pipeline of specialized AI agents** — locator, planner, requirement/coverage, organization, test-code generation, execution, and selector-healing — to:
   - discover page elements and build reliable locators,
   - create a structured test plan with prioritized scenarios,
   - generate Playwright TypeScript test files with page objects,
   - check for and resolve duplicate scenarios against a central registry,
   - and re-run / heal broken selectors automatically.
3. **Generates complete manual test suites** with typed cases (happy path, negative, edge case, smoke, regression, usability, security, performance), saved as structured JSON and browsable in the UI.
4. **Runs everything in one place** — a browser-based UI and an optional Electron desktop shell, backed by a FastAPI server.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend API | Python 3.10+, FastAPI, Uvicorn |
| AI Agents | OpenAI SDK with multi-provider support (OpenAI, Anthropic Claude, Google Gemini, Groq, Ollama, GitHub Copilot) |
| UI | React 18 + Vite |
| Desktop shell | Electron (with auto-started backend process) |
| Legacy desktop UI | PySide6 (Qt) |
| Automation runtime | Playwright (Node) |
| Document parsing | python-docx, openpyxl, PyPDF, BeautifulSoup, Markdown |
| Data | JSON-based registry & suites (no database required) |

## How to Run

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** (tested with Node 22)
- **Git Bash / WSL** only required for the optional full desktop packaging (`npm run build`)
- An **LLM provider** — OpenAI, Anthropic, Google, Groq, Ollama, or a VS Code GitHub Copilot subscription

### 1. Install dependencies

```bash
# Python backend
pip install -r requirements.txt

# Install Playwright browsers (needed to run automated tests)
python -m playwright install chromium

# Node dependencies (root package.json runs `cd frontend && npm install` automatically)
npm install
```

### 2. Configure the AI provider

Open **Settings** (gear icon, top-right) and choose a provider:

- **OpenAI / Anthropic / Google / Groq** — enter your API key and pick a model.
- **Ollama (Local)** — enter the base URL (default `http://localhost:11434`); models load automatically.
- **VS Code GitHub Copilot** — no key required; the token is auto-detected from `COPILOT_GITHUB_TOKEN`, `GITHUB_TOKEN`, `GH_TOKEN`, or the `gh` CLI. Needs a fine-grained PAT with **Copilot Requests** permission.

> Environment variables can also be used: `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `OLLAMA_BASE_URL`, `OUTPUT_DIR`, `PORT` (default `8765`).

### 3. Start the application

```bash
# Option A — Browser mode (recommended): starts frontend (http://localhost:5175)
# and auto-starts the backend (http://localhost:8765) together.
npm run dev:frontend
```

Then open **http://localhost:5175** in your browser.

```bash
# Option B — Electron desktop app: starts frontend + backend + opens a native window.
npm run dev
```

```bash
# Option C — Backend only (API + interactive Swagger docs at http://localhost:8765/docs)
npm run dev:backend
```

### 4. (Optional) Package as a desktop app

```bash
npm run build      # bundles backend with PyInstaller, builds frontend, packages with electron-builder
# or just build the frontend and package:
npm run dist
```

## User Manual

### Screen overview

Two main tabs plus a Settings gear and a User Manual button (F1):

- **Automation Tests** — generates and manages Playwright automation.
- **Manual Tests** — generates structured, human-executable test suites.
- **Settings (gear)** — configure AI provider, model, output directory, and Atlassian integrations.
- **User Manual (?)** — in-app help.

### Automation Tests tab

**Fresh Generate** — the primary workflow:

1. Fill in one or more context sources:
   - **Application URL** — the app is crawled to discover pages and elements.
   - **Codebase Path** — point to a source repository to infer routes, components, and element hints.
   - **Requirement Text** — paste the feature description.
   - Optional: PRD file, OpenAPI spec, env file, Confluence URL, Jira ticket/sprint/project.
2. Click **Generate Tests**.
3. The pipeline runs: context ingest → locators → test plan → scenario extraction (+ AI coverage amplification) → duplicate check → organization → test code + page objects.
4. Review the results panel: **Test Plan**, **Locators**, **Scenarios**, **Test Code**, and the generated **file paths** under your output directory (`tests/`, `pages/`).
5. Playwright is auto-scaffolded at the output directory on first use.

**Add Feature** — generates tests for an additional feature in the same project.

**Modify Tests** — regenerates/extends an existing test file (enter the test file name).

**Test Registry** — central store of all generated scenarios; used to detect and resolve duplicates across features.

### Manual Tests tab

**Fresh Generate:**

1. Enter a **Feature Name** (required) and, optionally, an application URL, requirement text, PRD file, Confluence URL, or Jira ticket.
2. Click **Generate Manual Tests**.
3. The agent produces a full suite covering happy path, negative, edge case, and smoke scenarios (plus more when the source material warrants), saved to `<output-dir>/manual-tests/<feature-slug>.json`.
4. The results panel shows **Added / Edited / Total** counts and each generated case with priority, test type, preconditions, steps, expected result, and tags.

**Add Feature** — appends new cases to an existing suite (skips cases that already exist by title).

**Edit Tests** — regenerates a suite, merging with the existing file (specify the existing `feature-slug.json`).

**View Suites** — lists every generated suite (feature, version, dates, case count) and lets you open and inspect the cases.

### Settings

- **AI Provider** — provider, model, custom-model persistence, max output tokens slider (512–16384), and API key / Ollama base URL / Copilot token fields.
- **Test Output Directory** — where all generated artifacts are written. Use **Browse** for a native-style folder picker that shows the full selected path, or **Open in Explorer**.
- **Atlassian Integration** — Jira and Confluence credentials/URLs for fetching ticket and page content as test context.

### Outputs

When you configure an output directory, AI QA Platform writes:

```
<output-dir>/
├── manual-tests/            # manual test suites (one JSON per feature)
│   └── user-authentication.json
├── tests/                   # generated Playwright TypeScript tests
│   ├── test_registry.json   # scenario registry (duplicate detection)
│   └── ...
├── pages/                   # generated page objects
├── reports/                 # test run reports
├── package.json             # Playwright project scaffold
├── playwright.config.ts
└── tsconfig.json
```

### Keyboard shortcuts & tips

- **F1** — open the User Manual.
- **Ctrl+,** — open Settings.
- Ports: frontend `5175`, backend `8765`. Backend Swagger UI: `http://localhost:8765/docs`.
- If a manual test run returns only a few generic cases, check that your provider/model/key is set in Settings and raise **Max Output Tokens** (e.g., 4096+).

## Project Structure

```
TestGeneration/
├── backend/                  # FastAPI backend
│   ├── app.py                # API routes (port 8765)
│   ├── orchestrator.py       # automation pipeline orchestration
│   ├── agents/               # AI agents (locator, planner, requirement,
│   │   │                     #   organization, test, execution, healing, manual_test)
│   │   └── skills/           # prompt/skill files (.skill.md)
│   ├── services/             # generators, registry, duplicate detection, crawler, etc.
│   ├── ingestion/            # context sources (PRD, Jira, Confluence, OpenAPI, codebase)
│   ├── models/               # Pydantic schemas
│   └── utils/                # file writer, JSON parsing, skill loader
├── frontend/                 # React + Vite UI (port 5175)
├── electron/                 # Electron shell + backend process manager
├── frontend_pyqt/            # legacy PySide6 desktop UI
├── requirements.txt          # Python dependencies
└── package.json              # Node scripts (dev, dev:frontend, dev:backend, dist)
```

## API Endpoints (summary)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health |
| POST | `/generate-tests` | Fresh / add / modify automation generation |
| POST | `/run-tests` | Execute generated Playwright tests |
| POST | `/manual-tests` | Generate / add / edit manual test suites |
| GET | `/manual-tests` | List manual test suites |
| GET | `/manual-tests/{slug}` | Get a manual test suite |
| GET | `/registry` | List test registry entries |
| POST | `/config` | Set output directory |
| GET | `/config` | Get configuration |
| POST | `/setup-playwright` | Scaffold Playwright at the output directory |
| GET | `/browse-directories` | List directories (folder picker) |
| POST | `/test-atlassian-credentials` | Validate Jira/Confluence credentials |

---

