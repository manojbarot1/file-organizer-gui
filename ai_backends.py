import requests
import time
from typing import List

# Request timeouts
OLLAMA_TIMEOUT = 30
API_TIMEOUT = 60


def list_ollama_models() -> List[str]:
    """Return available Ollama models from the local daemon."""
    try:
        url = "http://localhost:11434/api/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        names = [m["name"] for m in models if isinstance(m, dict) and "name" in m]
        return sorted(names)
    except Exception:
        return []


def _ollama_generate(model: str, prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 64,
            "stop": ["\n\n", "Path:", "Folder:", "Directory:"],
            "num_ctx": 4096,
        },
    }
    response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()
    result = response.json()
    return (result.get("response") or "").strip()


def query_ollama(model: str, prompt: str) -> str:
    try:
        return _with_retry(lambda: _ollama_generate(model, prompt))
    except Exception as exc:
        return f"Error: {exc}"


def _openai_chat(api_key: str, model: str, prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a file organization expert. Respond only with folder paths."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 64,
        "temperature": 0.1,
        "stop": ["\n\n", "Path:", "Folder:"],
    }
    response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if choices:
        return (choices[0].get("message", {}).get("content") or "").strip()
    return "Error: No response from OpenAI"


def query_openai(model: str, prompt: str, api_key: str) -> str:
    try:
        return _with_retry(lambda: _openai_chat(api_key, model, prompt))
    except Exception as exc:
        return f"Error: {exc}"


def _grok_chat(api_key: str, model: str, prompt: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a file organization assistant. Reply only with folder paths."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 64,
        "temperature": 0.1,
        "stop": ["\n\n", "Path:", "Folder:"],
    }
    response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if choices:
        return (choices[0].get("message", {}).get("content") or "").strip()
    return "Error: No response from Grok"


def query_grok(model: str, prompt: str, api_key: str) -> str:
    try:
        return _with_retry(lambda: _grok_chat(api_key, model, prompt))
    except Exception as exc:
        return f"Error: {exc}"


def test_ai_connection(backend: str, model: str, api_key: str = "") -> tuple[bool, str]:
    """Quick check that a backend responds."""
    test_prompt = "Organize file 'test.txt' (plain text). Respond only with a folder path."
    try:
        if backend == "Local (Ollama)":
            if not model:
                return False, "No model selected"
            # ping daemon
            try:
                requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()
            except Exception:
                return False, "Ollama not reachable on localhost:11434"
            out = query_ollama(model, test_prompt)
            return (not out.startswith("Error:"), out)
        if backend == "OpenAI":
            if not api_key or not model:
                return False, "Missing API key or model"
            out = query_openai(model, test_prompt, api_key)
            return (not out.startswith("Error:"), out)
        if backend == "Grok":
            if not api_key or not model:
                return False, "Missing API key or model"
            out = query_grok(model, test_prompt, api_key)
            return (not out.startswith("Error:"), out)
    except Exception as exc:
        return False, str(exc)
    return False, "Unsupported backend"


def optimize_prompt_for_backend(backend: str, base_prompt: str) -> str:
    if backend == "Local (Ollama)":
        return base_prompt + "\n\nRespond ONLY with the folder path on one line:"
    if backend == "OpenAI":
        return (
            "As a file organization expert, choose the best folder path.\n\n"
            + base_prompt
            + "\nRules:\n- Respond ONLY with the folder path\n- Use forward slashes\n- Max depth 3\n- If uncertain, use 'Uncategorized'\n\nPath:"
        )
    if backend == "Grok":
        return (
            "File organization task. Return ONLY the folder path (one line).\n\n"
            + base_prompt
            + "\nONLY path:"
        )
    return base_prompt


def _with_retry(fn, max_retries: int = 2, delay: float = 0.8) -> str:
    last_err = "Error: Unknown"
    for attempt in range(max_retries + 1):
        try:
            out = fn()
            if not (isinstance(out, str) and out.startswith("Error:")):
                return out
            last_err = out
        except Exception as exc:
            last_err = f"Error: {exc}"
        if attempt < max_retries:
            time.sleep(delay)
    return last_err


def validate_folder_path(path: str) -> str:
    if not path or path.lower() in {"error", "none", "null"}:
        return "Uncategorized"
    text = path.strip()
    # strip common surrounding quotes/backticks
    if text and text[0] in {'"', "'", "`"} and text[-1:] == text[0]:
        text = text[1:-1]
    text = text.replace("\\", "/").strip("/")
    for ch in '<>:"|?*':
        text = text.replace(ch, "")
    parts = [p for p in text.split("/") if p]
    return "/".join(parts[:3]) or "Uncategorized"

