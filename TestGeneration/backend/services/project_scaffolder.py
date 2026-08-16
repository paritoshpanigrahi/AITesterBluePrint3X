import os
import json
import subprocess
import shlex


PLAYWRIGHT_CONFIG_TS = '''import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.TEST_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
'''

PACKAGE_JSON_TPL = {
    "name": "ai-qa-generated-tests",
    "private": True,
    "scripts": {
        "test": "playwright test",
        "test:headed": "playwright test --headed",
        "test:debug": "playwright test --debug",
    },
    "devDependencies": {
        "@playwright/test": "^1.50.0",
        "typescript": "^5.7.0",
    },
}

TSCONFIG_JSON = {
    "compilerOptions": {
        "target": "ES2022",
        "module": "commonjs",
        "lib": ["ES2022"],
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "resolveJsonModule": True,
    },
    "include": ["./tests/**/*.ts", "./pages/**/*.ts"],
}


class ProjectScaffolder:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def check(self):
        result = {
            "playwright_installed": False,
            "npm_found": False,
            "output_dir": os.path.abspath(self.output_dir),
            "message": "",
        }

        npm = self._find_cmd(["npm", "npm.cmd"])
        if npm:
            result["npm_found"] = True

        if self._project_exists():
            result["playwright_installed"] = True
            result["message"] = "Playwright project already exists"
            return result

        if not npm:
            result["message"] = "npm not found. Install Node.js to set up Playwright."
            return result

        result["message"] = "Playwright is not set up. Setup is required before running tests."
        return result

    def ensure(self, user_consent=False):
        if self._project_exists():
            return {"scaffolded": False, "message": "Playwright project already exists"}

        if not user_consent:
            return {
                "scaffolded": False,
                "setup_required": True,
                "message": "Playwright setup is required. Call again with setup_playwright=True or use /setup-playwright endpoint.",
            }

        result = self._scaffold()
        return result

    def _project_exists(self):
        # Strict check: Playwright is usable only if node_modules exist
        if os.path.isdir(os.path.join(self.output_dir, "node_modules", "@playwright", "test")):
            return True
        # Or if package.json declares the dependency (npm install can fulfill it)
        pkg_path = os.path.join(self.output_dir, "package.json")
        if os.path.isfile(pkg_path):
            try:
                with open(pkg_path, "r") as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "@playwright/test" in deps:
                    return True
            except Exception:
                pass
        return False

    def _scaffold(self):
        os.makedirs(self.output_dir, exist_ok=True)

        pkg_path = os.path.join(self.output_dir, "package.json")
        if os.path.isfile(pkg_path):
            # Merge @playwright/test into existing package.json
            with open(pkg_path, "r") as f:
                existing = json.load(f)
            existing.setdefault("devDependencies", {})
            if "@playwright/test" not in existing["devDependencies"]:
                existing["devDependencies"]["@playwright/test"] = PACKAGE_JSON_TPL["devDependencies"]["@playwright/test"]
                existing["devDependencies"]["typescript"] = PACKAGE_JSON_TPL["devDependencies"]["typescript"]
                existing.setdefault("scripts", {})
                if "test" not in existing["scripts"]:
                    existing["scripts"]["test"] = "playwright test"
                if "test:headed" not in existing["scripts"]:
                    existing["scripts"]["test:headed"] = "playwright test --headed"
            with open(pkg_path, "w") as f:
                json.dump(existing, f, indent=2)
        else:
            with open(pkg_path, "w") as f:
                json.dump(PACKAGE_JSON_TPL, f, indent=2)

        config_path = os.path.join(self.output_dir, "playwright.config.ts")
        if not os.path.isfile(config_path):
            with open(config_path, "w") as f:
                f.write(PLAYWRIGHT_CONFIG_TS)

        tsconfig_path = os.path.join(self.output_dir, "tsconfig.json")
        if not os.path.isfile(tsconfig_path):
            with open(tsconfig_path, "w") as f:
                json.dump(TSCONFIG_JSON, f, indent=2)

        os.makedirs(os.path.join(self.output_dir, "tests"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "pages"), exist_ok=True)

        npm_ok, npm_msg = self._run_npm_install()
        if not npm_ok:
            return {"scaffolded": False, "message": npm_msg}

        browser_ok, browser_msg = self._install_browsers()

        return {
            "scaffolded": True,
            "message": "Playwright project scaffolded",
            "npm_install": npm_msg,
            "browser_install": browser_msg if browser_ok else "Skipped or failed",
        }

    def _find_cmd(self, names):
        for name in names:
            try:
                r = subprocess.run(
                    [name, "--version"],
                    capture_output=True, text=True, timeout=10
                )
                if r.returncode == 0:
                    return name
            except Exception:
                continue
        return None

    def _run_npm_install(self):
        npm = self._find_cmd(["npm", "npm.cmd"])
        if not npm:
            return False, "npm not found. Install Node.js to install Playwright dependencies."

        try:
            result = subprocess.run(
                [npm, "install"],
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=120000,
            )
            if result.returncode != 0:
                logs = (result.stderr or result.stdout)[:500]
                return False, f"npm install failed: {logs}"
            return True, "Dependencies installed"
        except subprocess.TimeoutExpired:
            return False, "npm install timed out after 120s"
        except Exception as e:
            return False, f"npm install error: {str(e)}"

    def _install_browsers(self):
        npx = self._find_cmd(["npx", "npx.cmd"])
        if not npx:
            return False, "npx not found"
        try:
            subprocess.run(
                [npx, "playwright", "install", "chromium"],
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=120000,
            )
            return True, "Chromium browser installed"
        except Exception:
            return False, "Browser install skipped"
