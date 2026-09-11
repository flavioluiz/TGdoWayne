# Executed read-only after explicit ROOT CLOSED-summary/completion signal.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python tmp/c07_synthesis_independent_review/audit_synthesis.py \
 --summary results/C07/synthesis/summary.json --arrays results/C07/synthesis/arrays.npz \
 --tests results/C07/synthesis/tests.csv --paired results/C07/synthesis/paired_central90.csv \
 --config configs/calibration/sbc_synthesis_v1.json \
 --complete tmp/c07_posterior500_v1/campaign_complete.json --plan tmp/c07_posterior500_v1/campaign_plan.json \
 --expected-summary-sha 909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a \
 --expected-complete-sha 1daa0948e9d55f6537cd7c25870c609ea9e1c8019dc59dc8abea899ff6b2c9e2 \
 --output tmp/c07_synthesis_independent_review/closed500
# Additional compact NPZ reading was explicitly authorized; no raw reading.
.venv/bin/python tmp/c07_synthesis_independent_review/audit_resolution.py \
 --diagnostics tmp/c07_posterior500_v1/diagnostics \
 --summary results/C07/synthesis/summary.json --arrays results/C07/synthesis/arrays.npz \
 --complete tmp/c07_posterior500_v1/campaign_complete.json \
 --protocol configs/calibration/campaign_diagnostics_v1.json \
 --expected-summary-sha 909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a \
 --expected-complete-sha 1daa0948e9d55f6537cd7c25870c609ea9e1c8019dc59dc8abea899ff6b2c9e2 \
 --output tmp/c07_synthesis_independent_review/resolution500
.venv/bin/python tmp/c07_synthesis_independent_review/resolution_causes.py
# Output directories are immutable; replay must use separate new destinations.
