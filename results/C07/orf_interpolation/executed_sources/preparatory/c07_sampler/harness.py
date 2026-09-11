from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from inference.model import experiment
CONFIG=ROOT/'configs/calibration/pilot_initial.json'
DATA=ROOT/'tmp/c07_integration/results/data.npz'
def load():
    cfg=json.loads(CONFIG.read_text()); e=experiment(cfg)
    with np.load(DATA) as f:data={k:f[k] for k in f.files}
    return cfg,e,data
