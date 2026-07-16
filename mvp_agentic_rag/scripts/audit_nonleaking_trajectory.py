from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.nonleaking_musique import audit_nonleaking_trajectory


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit blinded trajectories without reading gold for actions.")
    parser.add_argument("trajectory")
    parser.add_argument("--labels")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    result = audit_nonleaking_trajectory(args.trajectory, labels_path=args.labels)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
