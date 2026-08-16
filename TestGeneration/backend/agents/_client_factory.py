import os
import json
import json5
import re
import asyncio
import sys
from openai import AsyncOpenAI

PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq": "https://api.groq.com/openai/v1",
    "github-copilot": "https://api.githubcopilot.com/v1",
    "ollama": None,
}

_llm_provider = ""
_llm_api_key = ""
_llm_model = ""
_llm_max_tokens = 2048
_llm_max_input_chars = 100000
_llm_errors = []


def configure(provider="", api_key="", model="", max_tokens=0):
    global _llm_provider, _llm_api_key, _llm_model, _llm_max_tokens
    if provider:
        _llm_provider = provider
    if api_key:
        _llm_api_key = api_key
    if model:
        _llm_model = model
    if max_tokens:
        _llm_max_tokens = max_tokens


def make_client(api_key="", model="", provider=""):
    p = provider or _llm_provider or os.getenv("LLM_PROVIDER", "openai")
    key = api_key or _llm_api_key or os.getenv("OPENAI_API_KEY", "")
    effective_model = model or _llm_model or os.getenv("OPENAI_MODEL", "gpt-4o")

    if p == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1"
    else:
        base_url = PROVIDER_BASE_URLS.get(p) or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    return AsyncOpenAI(api_key=key, base_url=base_url), effective_model


def format_llm_error(e):
    err_str = str(e) if str(e) else repr(e)
    err_lower = err_str.lower()

    if isinstance(e, asyncio.TimeoutError):
        return {
            "type": "timeout",
            "message": "The AI provider took too long to respond (asyncio timeout).",
            "suggestion": "Try a faster model, reduce input size, or check your internet connection.",
        }
    if "401" in err_str or "unauthorized" in err_lower or "invalid_api_key" in err_lower:
        return {
            "type": "auth_error",
            "message": "Invalid API key or authentication failed.",
            "suggestion": "Check your API key in Settings and ensure it is correct for the selected provider.",
        }
    if "404" in err_str or "model_not_found" in err_lower or "does not exist" in err_lower:
        return {
            "type": "model_not_found",
            "message": "The selected model is not available on your account.",
            "suggestion": "Choose a different model in Settings. Check the provider console for which models your account can access.",
        }
    if "413" in err_str or "rate_limit" in err_lower or "too large" in err_lower or "tokens per minute" in err_lower:
        return {
            "type": "rate_limit",
            "message": "Request exceeded the provider rate or token limit.",
            "suggestion": "Wait a moment and try again, reduce the input size, or upgrade to a paid tier for higher limits.",
        }
    if "429" in err_str or "too many requests" in err_lower:
        return {
            "type": "rate_limit",
            "message": "Too many requests sent to the provider.",
            "suggestion": "Wait a moment and try again. Rate limits reset after a short time.",
        }
    if "timeout" in err_lower or "timed out" in err_lower:
        return {
            "type": "timeout",
            "message": "The AI provider took too long to respond.",
            "suggestion": "Try a faster model or check your internet connection.",
        }
    return {
        "type": "unknown",
        "message": f"An unexpected error occurred: {err_str[:300]}",
        "suggestion": "Check your LLM settings (provider, model, API key) and try again. If the issue persists, try a different provider or model.",
    }


def record_llm_error(error_info):
    _llm_errors.append(error_info)


def get_and_clear_llm_errors():
    global _llm_errors
    errors = _llm_errors[:]
    _llm_errors = []
    return errors


def _try_parse_json(text):
    text = text.strip()
    idx = text.find('{')
    if idx == -1:
        idx = text.find('[')
    if idx == -1:
        return None
    text = text[idx:]
    depth = 0
    start_ch = text[0]
    end_ch = '}' if start_ch == '{' else ']'
    for i, ch in enumerate(text):
        if ch == start_ch:
            depth += 1
        elif ch == end_ch:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[:i+1])
                except json.JSONDecodeError:
                    try:
                        return json5.loads(text[:i+1])
                    except Exception:
                        return None
    return None


def extract_json(text):
    raw = text
    text = text.strip()

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        lines = text.split("\n")
        start = 0
        for i, line in enumerate(lines):
            if line.startswith("```"):
                start = i + 1
                break
        end = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end]).strip()

    # Try direct brace/bracket-based parsing first
    result = _try_parse_json(text)
    if result is not None:
        return result

    # Fallback: regex search for JSON object or array in text
    json_patterns = [
        (r'(\{.*?\})', re.DOTALL),
        (r'(\[.*?\])', re.DOTALL),
    ]
    for pattern, flags in json_patterns:
        for match in re.finditer(pattern, text, flags):
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                try:
                    return json5.loads(candidate)
                except Exception:
                    continue

    snippet = raw[:500]
    print(f"[EXTRACT_JSON ERROR] No valid JSON found. Response preview (first 500 chars):\n{snippet}\n", file=sys.stderr)
    raise ValueError(f"No JSON object or array found in response. Response preview: {snippet[:200]}...")


def _truncate_prompts(system_prompt, user_prompt, max_input_chars):
    """Truncate prompts to fit within max_input_chars, preferring to keep system prompt intact."""
    combined = system_prompt + "\n" + user_prompt
    if len(combined) <= max_input_chars:
        return system_prompt, user_prompt

    sys_len = len(system_prompt)
    # If system prompt alone exceeds the budget, truncate it too
    if sys_len >= max_input_chars:
        keep = max_input_chars - 200
        system_prompt = system_prompt[:keep] + "\n\n[system prompt truncated...]"
        return system_prompt, "[user prompt omitted due to system prompt size]"

    user_budget = max_input_chars - sys_len
    if len(user_prompt) <= user_budget:
        return system_prompt, user_prompt
    user_prompt = user_prompt[:user_budget] + "\n\n[content truncated to fit token budget...]"
    return system_prompt, user_prompt


async def call_llm(system_prompt, user_prompt, api_key="", model="", temperature=0.3, max_tokens=16384, timeout=300):
    effective_max_tokens = min(max_tokens, _llm_max_tokens) if _llm_max_tokens else max_tokens
    system_prompt, user_prompt = _truncate_prompts(system_prompt, user_prompt, _llm_max_input_chars)

    client, effective_model = make_client(api_key, model)
    last_error = None
    for attempt in range(4):
        try:
            coro = client.chat.completions.create(
                model=effective_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=effective_max_tokens,
            )
            response = await asyncio.wait_for(coro, timeout=timeout)
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_info = format_llm_error(e)
            is_rate_limit = error_info["type"] == "rate_limit"
            is_auth = error_info["type"] == "auth_error"
            is_model = error_info["type"] == "model_not_found"
            if is_rate_limit and attempt < 3:
                wait = (attempt + 1) * 15
                import sys; print(f"[LLM RETRY] rate limited, retrying in {wait}s (attempt {attempt+1}/3)", file=sys.stderr)
                await asyncio.sleep(wait)
                last_error = error_info
                continue
            record_llm_error(error_info)
            raise
    record_llm_error(last_error)
    raise Exception("LLM call failed after 3 retries")
