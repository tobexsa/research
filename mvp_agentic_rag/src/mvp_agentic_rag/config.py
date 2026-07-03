from __future__ import annotations

from pathlib import Path


def load_simple_config(path: str | Path) -> dict:
    config = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
            config[key] = items
        elif value.isdigit():
            config[key] = int(value)
        elif value.lower() in {"true", "false"}:
            config[key] = value.lower() == "true"
        else:
            config[key] = value.strip("'\"")
    return config
