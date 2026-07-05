"""Tiny stdlib-only HTTP client for OpenRouter (no `requests` dependency)."""
import json, urllib.request, urllib.error


def _request(url, api_key, body):
    data = json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return urllib.request.Request(url, data=data, headers=headers, method="POST")


def http_detail(e):
    """Readable message for an HTTPError (status + a snippet of the body)."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            body = ""
        return f"HTTP {e.code} {e.reason}: {body}"
    return f"{type(e).__name__}: {e}"


def stream_lines(url, api_key, body, timeout=180):
    """Yield decoded SSE lines (e.g. 'data: {...}'). Raises RuntimeError on HTTP error."""
    req = _request(url, api_key, body)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise RuntimeError(http_detail(e))
    try:
        for raw in resp:
            yield raw.decode("utf-8", "replace").rstrip("\r\n")
    finally:
        resp.close()


def post_json(url, api_key, body, timeout=180):
    """Non-streaming POST -> parsed JSON. Raises RuntimeError on HTTP error."""
    req = _request(url, api_key, body)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(http_detail(e))
