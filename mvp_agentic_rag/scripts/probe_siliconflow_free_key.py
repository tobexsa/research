from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.env import load_env_file


KEY_ENV = "SILICONFLOW_API_KEY_FREE"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
URL = "https://api.siliconflow.cn/v1/chat/completions"


def main() -> int:
    load_env_file(ROOT / ".env")
    api_key = os.environ.get(KEY_ENV, "")
    if not api_key:
        print(f"ERROR: {KEY_ENV} is missing or empty.", file=sys.stderr)
        return 2

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly OK."}],
        "temperature": 0.0,
        "max_tokens": 8,
    }
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"HTTP {response.status}")
            print(_redact(body, api_key))
            return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} {exc.reason}", file=sys.stderr)
        print(_redact(body, api_key), file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"NETWORK ERROR: {exc}", file=sys.stderr)
        return 1


def _redact(text: str, api_key: str) -> str:
    return text.replace(api_key, "<redacted-api-key>") if api_key else text


if __name__ == "__main__":
    raise SystemExit(main())
