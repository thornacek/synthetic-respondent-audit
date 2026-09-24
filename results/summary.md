# Results

Model: claude-haiku-4-5-20251001
Cells: 120 | Calls scored: 360 | Parse failures: 0

**Primary: interval coverage (run 1, one observation per cell)**
44/120 = 36.7% (95% Wilson CI 28.6 to 45.6) against a promised 80%.

**Accuracy**
Mean absolute error 8.6 pts (median 7.1).
Mean signed error +5.1 pts (positive = model overstates the counted answer).
Mean interval width 10.5 pts. Mean run-to-run SD 1.6 pts.

**Contamination check: total vs. subgroup cells (run 1 coverage, mean absolute error)**
- total population: coverage 20% (n=20), MAE 9.5 pts
- subgroups: coverage 40% (n=100), MAE 8.4 pts

**Error drivers (Shapley share of R² = 0.16)**
- topic domain: 66%
- subgroup: 17%
- how lopsided the true answer is: 16%
- cell base size (log): 1%