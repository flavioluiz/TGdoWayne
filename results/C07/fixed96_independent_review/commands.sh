# Executed only after ROOT confirmed both fixed96 and synthesis processes closed.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python tmp/c07_fixed_independent_review/audit_fixed.py \
 --summary results/C07/fixed_synthesis/summary.json \
 --arrays results/C07/fixed_synthesis/arrays.npz \
 --campaign tmp/c07_fixed_posterior96_v2 \
 --synthesis-config configs/calibration/fixed_synthesis_v1.json \
 --numerical-protocol tmp/c07_fixed_scenarios/configs/fixed_diagnostics_v1.json \
 --scientific-protocol configs/calibration/fixed_scenarios_v1.json \
 --experiment configs/calibration/fixed_experiment_v1.json \
 --data results/C07/fixed_scenarios/data.npz \
 --generation results/C07/fixed_scenarios/generation.json \
 --expected-summary-sha 1273de6e7f2b835a5c349c5df243b60ac5f865ff0f55f61bfb2715e0ac0c11d5 \
 --expected-complete-sha 70b3da6322bc99f4ccd172a86577efb22b9fe37221bd504044af174f7452b2b1 \
 --output tmp/c07_fixed_independent_review/closed96
# Replays need a new output path; existing reviews are never overwritten.
