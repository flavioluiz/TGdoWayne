"""Explicit root paths for the frozen selected A0 reference; no source-tree outputs."""
from pathlib import Path
import os

def repository_root():
    explicit=os.environ.get('TGWAYNE_REFERENCE_ROOT')
    candidates=[Path(explicit).resolve()] if explicit else [Path.cwd(),*Path(__file__).resolve().parents]
    for root in candidates:
        if (root/'configs/calibration/pilot_initial.json').exists():return root
    raise RuntimeError('Set TGWAYNE_REFERENCE_ROOT to the repository with the frozen pilot config.')
ROOT=repository_root()
CONFIG=ROOT/'configs/calibration/pilot_initial.json'
DATA=ROOT/'results/C07/fixtures/pilot_data.npz'
ORF_CACHE=ROOT/'results/C07/fixtures/orf_cache'
CUT_SOURCE=ROOT/'results/C07/pilot_initial/endpoint_129_13_independent.json'
OUTPUT=ROOT/'results/C07/reference'
FROZEN_CUBATURE_RESULTS=OUTPUT/'cubature'
FROZEN_QUANTILE_RESULTS=OUTPUT/'quantiles'
CUBATURE_RESULTS=OUTPUT/'reproduced/cubature'
QUANTILE_RESULTS=OUTPUT/'reproduced/quantiles'
