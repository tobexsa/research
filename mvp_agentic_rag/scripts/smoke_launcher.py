from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(r"D:\research\mvp_agentic_rag")
CFG = ROOT / r"configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_2_4_pre_final_slot_gate_smoke1_local_api_no_think.yaml"
OUT = ROOT / r"runs\logs\smoke1_launcher.out.log"
ERR = ROOT / r"runs\logs\smoke1_launcher.err.log"


def main() -> int:
    with OUT.open("w", encoding="utf-8") as out, ERR.open("w", encoding="utf-8") as err:
        proc = subprocess.Popen(
            [sys.executable, r"scripts\run_layer1_skeleton.py", "--config", str(CFG)],
            cwd=str(ROOT),
            stdout=out,
            stderr=err,
            env=os.environ.copy(),
        )
        print(proc.pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
