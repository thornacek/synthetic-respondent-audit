"""Score model estimates against GSS truth. Writes results/.

Usage:
  python src/score.py          scores data/estimates.jsonl
  python src/score.py --mock   scores the MOCK file; every output is stamped MOCK
"""
import itertools
import json
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import INTERVAL

MOCK = "--mock" in sys.argv
TAG = "_MOCK" if MOCK else ""
STAMP = "  [MOCK DATA: PIPELINE TEST, NOT A RESULT]" if MOCK else ""
OUT = pathlib.Path("results")
OUT.mkdir(exist_ok=True)

truth = pd.read_csv("data/truth.csv")
recs = [json.loads(l) for l in pathlib.Path(f"data/estimates{TAG}.jsonl").read_text().splitlines()]
est = pd.DataFrame([{**{k: r[k] for k in ("item", "subgroup", "run", "model")}, **(r["parsed"] or {}),
                     "parse_ok": r["parsed"] is not None} for r in recs])
calls = est.merge(truth, on=["item", "subgroup"])
parse_fail = int((~calls["parse_ok"]).sum())
calls = calls[calls["parse_ok"]].copy()
calls["low"], calls["high"] = calls[["low", "high"]].min(axis=1), calls[["low", "high"]].max(axis=1)
calls["covered"] = (calls["truth_pct"] >= calls["low"]) & (calls["truth_pct"] <= calls["high"])
calls["abs_err"] = (calls["estimate"] - calls["truth_pct"]).abs()
calls["width"] = calls["high"] - calls["low"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


# Primary analysis (pre-registered): run 1 only, one observation per cell.
primary = calls[calls["run"] == 1]
k, n = int(primary["covered"].sum()), len(primary)
cov, lo, hi = wilson(k, n)

# Cell level: mean across runs, plus run-to-run spread (consistency).
cells = calls.groupby(["item", "subgroup", "domain", "n_eff", "truth_pct"], as_index=False).agg(
    est_mean=("estimate", "mean"), est_sd=("estimate", "std"), width_mean=("width", "mean"),
    covered_run1=("covered", "first"))
cells["abs_err"] = (cells["est_mean"] - cells["truth_pct"]).abs()
cells["extremity"] = (cells["truth_pct"] - 50).abs()
cells["log_n_eff"] = np.log(cells["n_eff"])
cells.to_csv(OUT / f"cells{TAG}.csv", index=False)

# Key driver analysis: exact Shapley decomposition of R-squared over predictor groups.
groups = {
    "topic domain": pd.get_dummies(cells["domain"], drop_first=True, dtype=float),
    "subgroup": pd.get_dummies(cells["subgroup"], drop_first=True, dtype=float),
    "cell base size (log)": cells[["log_n_eff"]],
    "how lopsided the true answer is": cells[["extremity"]],
}
y = cells["abs_err"].to_numpy()


def r2(names):
    if not names:
        return 0.0
    X = np.column_stack([np.ones(len(y))] + [groups[g].to_numpy() for g in names])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return 1 - resid.var() / y.var()


G = list(groups)
shap = {}
for g in G:
    others = [o for o in G if o != g]
    val = 0.0
    for r in range(len(others) + 1):
        for S in itertools.combinations(others, r):
            wgt = math.factorial(r) * math.factorial(len(G) - r - 1) / math.factorial(len(G))
            val += wgt * (r2(list(S) + [g]) - r2(list(S)))
    shap[g] = val
total_r2 = r2(G)

# Charts
by_dom = primary.groupby("domain")["covered"].agg(["sum", "count"])
w = [wilson(int(s), int(c)) for s, c in zip(by_dom["sum"], by_dom["count"])]
fig, ax = plt.subplots(figsize=(7, 4))
ps = [x[0] * 100 for x in w]
err = [[(x[0] - x[1]) * 100 for x in w], [(x[2] - x[0]) * 100 for x in w]]
ax.bar(by_dom.index, ps, yerr=err, capsize=6, color="#3b6ea8")
ax.axhline(INTERVAL * 100, ls="--", color="#b04a3a", label=f"promised coverage ({int(INTERVAL*100)}%)")
ax.set_ylabel("% of cells with truth inside the interval")
ax.set_ylim(0, 100)
ax.set_title("Does the model's stated uncertainty hold up?" + STAMP, fontsize=10)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / f"coverage_by_domain{TAG}.png", dpi=160)

fig, ax = plt.subplots(figsize=(7, 3.6))
share = pd.Series(shap).sort_values()
ax.barh(share.index, 100 * share / total_r2 if total_r2 > 0 else share, color="#3b6ea8")
ax.set_xlabel("% of explained variance in absolute error (Shapley)")
ax.set_title(f"What drives the misses? (model R² = {total_r2:.2f})" + STAMP, fontsize=10)
fig.tight_layout()
fig.savefig(OUT / f"error_drivers{TAG}.png", dpi=160)

fig, ax = plt.subplots(figsize=(5, 5))
for d, grp in cells.groupby("domain"):
    ax.scatter(grp["truth_pct"], grp["est_mean"], label=d, s=22)
ax.plot([0, 100], [0, 100], color="grey", lw=1)
ax.set_xlabel("GSS 2024 weighted %")
ax.set_ylabel("Model estimate % (mean of runs)")
ax.set_title("Estimate vs. survey truth" + STAMP, fontsize=10)
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(OUT / f"estimate_vs_truth{TAG}.png", dpi=160)

summary = f"""# Results{STAMP}

Model: {", ".join(sorted(calls["model"].unique()))}
Cells: {len(cells)} | Calls scored: {len(calls)} | Parse failures: {parse_fail}

**Primary: interval coverage (run 1, one observation per cell)**
{k}/{n} = {cov*100:.1f}% (95% Wilson CI {lo*100:.1f} to {hi*100:.1f}) against a promised {int(INTERVAL*100)}%.

**Accuracy**
Mean absolute error {cells['abs_err'].mean():.1f} pts (median {cells['abs_err'].median():.1f}).
Mean signed error {(cells['est_mean'] - cells['truth_pct']).mean():+.1f} pts (positive = model overstates the counted answer).
Mean interval width {cells['width_mean'].mean():.1f} pts. Mean run-to-run SD {cells['est_sd'].mean():.1f} pts.

**Contamination check: total vs. subgroup cells (run 1 coverage, mean absolute error)**
""" + "\n".join(
    f"- {lab}: coverage {wilson(int(s['covered_run1'].sum()), len(s))[0]*100:.0f}% "
    f"(n={len(s)}), MAE {s['abs_err'].mean():.1f} pts"
    for lab, s in [("total population", cells[cells["subgroup"] == "total"]),
                   ("subgroups", cells[cells["subgroup"] != "total"])]) + f"""

**Error drivers (Shapley share of R² = {total_r2:.2f})**
""" + "\n".join(f"- {g}: {100*v/total_r2:.0f}%" for g, v in share.sort_values(ascending=False).items())
(OUT / f"summary{TAG}.md").write_text(summary)
print(summary)
