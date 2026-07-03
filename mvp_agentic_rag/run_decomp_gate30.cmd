@echo off
cd /d "%~dp0"
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_decomp_gate_claim_risk_subset30.yaml
