@echo off
setlocal
cd /d D:\research\mvp_agentic_rag

D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2.yaml 1>runs\logs\layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2.out.log 2>runs\logs\layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2.err.log

set "EXIT_CODE=%ERRORLEVEL%"
echo Experiment exited with code %EXIT_CODE%.
exit /b %EXIT_CODE%
