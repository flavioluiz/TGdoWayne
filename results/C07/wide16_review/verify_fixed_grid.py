"""Independently reproduce the frozen 54-cut diagnostics; no new draws/logL."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import sys
import time

os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(a, b, path, differences, counters):
    if isinstance(a, dict):
        assert set(a) == set(b), path
        for key in a:
            compare(a[key], b[key], f"{path}.{key}", differences, counters)
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (aa, bb) in enumerate(zip(a, b)):
            compare(aa, bb, f"{path}[{i}]", differences, counters)
    elif isinstance(a, bool) or a is None or isinstance(a, str):
        assert a == b, (path, a, b)
        counters["exact_non_numeric_fields"] += 1
    elif isinstance(a, (float, int)):
        assert isinstance(b, (float, int)), (path, b)
        if math.isfinite(a) and math.isfinite(b):
            error = abs(a - b)
            differences.append((error, path))
            assert error <= 1e-12, (path, a, b, error)
        else:
            assert a == b or (math.isnan(a) and math.isnan(b)), (path, a, b)
        counters["numeric_fields"] += 1
    else:
        raise TypeError((path, type(a)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--grid", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.project_root / "src"))
    from inference.iid_optimized import TargetIIDContext
    from inference.iid_diagnostics import json_safe, simultaneous_differences
    grid = json.loads(args.grid.read_text())
    reference = json.loads(args.reference.read_text())
    assert sha(args.grid) == reference["frozen_grid_sha256"]
    start = time.perf_counter()
    differences = []
    counters = {"numeric_fields": 0, "exact_non_numeric_fields": 0}
    estimates, errors = {}, {}
    rows = []
    for n in (16384, 65536):
        with np.load(args.inputs / f"iid_N{n}.npz", allow_pickle=False) as f:
            # Truth members deliberately never read by this separate check.
            x, ll, lw, targets = (f[k] for k in ("x_unit", "log_likelihood", "log_weights", "targets"))
        estimates[n], errors[n] = [], []
        for k, target in enumerate(targets):
            cuts = next(t for t in grid["targets"] if t["target"] == target)["functions"]
            expected = next(r for r in reference["rows"] if r["target"] == target and r["N"] == n)
            ctx = TargetIIDContext(lw[:, :, k])
            actual = []
            for name in dict.fromkeys(c["function"] for c in cuts):
                group = [c for c in cuts if c["function"] == name]
                values = ll[:, :, k] if name == "log_likelihood" else x[:, :, k, int(name[-1])]
                results = ctx.cdf(values, [c["cdf"]["threshold"] for c in group])
                actual.extend(dict(function=name, probability=c["pilot_quantile_probability"], cdf=d)
                              for c, d in zip(group, results))
            compare(json_safe(actual), expected["functions"], f"N{n}.target{target}.functions", differences, counters)
            compare(json_safe(ctx.weights()), expected["weights"], f"N{n}.target{target}.weights", differences, counters)
            estimates[n].extend(c["cdf"]["estimate"] for c in actual)
            errors[n].extend(c["cdf"]["mcse"] for c in actual)
            rows.append(dict(N=n, target=int(target), cdf_count=len(actual),
                             precision_pass=sum(c["cdf"]["precision_pass"] for c in actual)))
    refinement = simultaneous_differences(estimates[16384], errors[16384], estimates[65536], errors[65536])
    compare(json_safe(refinement), reference["refinement"], "refinement", differences, counters)
    maximum = max(differences)
    output = dict(status="FIXED54_INDEPENDENT_REPRODUCTION_PASS_NOT_SBC500", rows=rows,
                  cdf_count=1728, high_level_cdf_count=864,
                  high_level_precision_pass=sum(r["precision_pass"] for r in rows if r["N"] == 65536),
                  checks=counters, maximum_absolute_field_difference=maximum[0],
                  maximum_difference_field=maximum[1], absolute_comparison_tolerance=1e-12,
                  all_non_numeric_fields_exact=True, uses_truth=False,
                  new_likelihood_evaluations=0, seconds=time.perf_counter() - start,
                  source_hashes={str(p): sha(p) for p in [Path(__file__), args.grid, args.reference,
                      args.project_root / "src/inference/iid_diagnostics.py",
                      args.project_root / "src/inference/iid_optimized.py"]})
    args.output.write_text(json.dumps(json_safe(output), indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k not in ["rows", "source_hashes"]}))


if __name__ == "__main__":
    main()
