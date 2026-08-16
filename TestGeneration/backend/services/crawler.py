class Crawler:
    async def crawl(self, url):
        if not url:
            return ""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                if resp.status_code == 200:
                    html = resp.text
                    return self._extract_elements(html)
                return f"Failed to fetch: HTTP {resp.status_code}"
        except Exception as e:
            return f"Error crawling {url}: {str(e)}"

    async def crawl_with_playwright(self, url):
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await page.wait_for_timeout(1000)
                html = await page.content()
                await browser.close()
                return self._extract_elements(html)
        except Exception as e:
            return f"Error with Playwright: {str(e)}"

    async def crawl_multiple(self, base_url, routes, auth=None):
        """
        Crawl multiple routes with Playwright, sharing a browser context.
        If auth is provided, logs in first so protected routes are accessible.

        auth: {"login_url": "/login", "username": "...", "password": "...",
               "username_selector": "#username", "password_selector": "#password",
               "submit_selector": "button[type='submit']"}
        Returns dict of {route: elements_string} for successful crawls.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {}
        results = {}
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720}
                )

                # Perform login if auth config provided
                if auth and auth.get("login_url") and auth.get("username"):
                    login_page = await context.new_page()
                    try:
                        login_url = base_url.rstrip('/') + auth["login_url"]
                        await login_page.goto(login_url, timeout=30000, wait_until="networkidle")
                        await login_page.wait_for_timeout(1000)
                        us = auth.get("username_selector", "#username")
                        ps = auth.get("password_selector", "#password")
                        ss = auth.get("submit_selector", "button[type='submit']")
                        await login_page.fill(us, auth["username"])
                        await login_page.fill(ps, auth.get("password", ""))
                        await login_page.click(ss)
                        await login_page.wait_for_load_state("networkidle")
                        await login_page.wait_for_timeout(2000)
                    except Exception:
                        pass
                    await login_page.close()

                for route in routes:
                    url = base_url.rstrip('/') + route
                    try:
                        page = await context.new_page()
                        await page.goto(url, timeout=30000, wait_until="networkidle")
                        await page.wait_for_timeout(1000)
                        html = await page.content()
                        elements = self._extract_elements(html)
                        if elements and len(elements) > 100:
                            results[route] = elements
                        await page.close()
                    except Exception:
                        pass
                await browser.close()
        except Exception:
            pass
        return results

    def _extract_elements(self, html):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            elements = []
            for tag in soup.find_all(["input", "button", "a", "select", "textarea", "form", "img", "h1", "h2", "h3", "nav", "header", "footer"]):
                el = {"tag": tag.name}
                for attr in ["id", "class", "name", "type", "placeholder", "aria-label", "data-testid", "href", "src", "alt", "role"]:
                    v = tag.get(attr)
                    if v:
                        el[attr] = v if attr != "class" else " ".join(v) if isinstance(v, list) else v
                text = tag.get_text(strip=True)[:100]
                if text:
                    el["text"] = text
                elements.append(el)
            return str(elements[:100])
        except Exception:
            return html[:5000]
