from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\research\mvp_agentic_rag")
CFG = ROOT / (
    r"configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_"
    r"five_stage_verifier_v1_2_5_pre_final_repair_closure_local_api_no_think.yaml"
)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / fr"runs\logs\v1_2_5_pre_final_repair_closure_{stamp}.out.log"
    err = ROOT / fr"runs\logs\v1_2_5_pre_final_repair_closure_{stamp}.err.log"
    with out.open("w", encoding="utf-8") as stdout, err.open("w", encoding="utf-8") as stderr:
        proc = subprocess.Popen(
            [sys.executable, r"scripts\run_layer1_skeleton.py", "--config", str(CFG)],
            cwd=str(ROOT),
            stdout=stdout,
            stderr=stderr,
            env=os.environ.copy(),
        )
        print(proc.pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
