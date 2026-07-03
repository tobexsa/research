@echo off
setlocal
cd /d "%~dp0.."

set "OUT_LOG=D:\research\mvp_agentic_rag\runs\logs\v1_2_4_pre_final_slot_gate_local_api_run1.out.log"
set "ERR_LOG=D:\research\mvp_agentic_rag\runs\logs\v1_2_4_pre_final_slot_gate_local_api_run1.err.log"
if exist "%OUT_LOG%" del /f /q "%OUT_LOG%"
if exist "%ERR_LOG%" del /f /q "%ERR_LOG%"

python scripts\run_layer1_skeleton.py --config configs\layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_2_4_pre_final_slot_gate_local_api_no_think.yaml 1>"%OUT_LOG%" 2>"%ERR_LOG%"
