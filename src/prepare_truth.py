"""Download GSS 2024 and compute weighted ground-truth percentages per cell.
Output: data/truth.csv (derived toplines only; raw microdata stays out of git)."""
import io
import pathlib
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import pyreadstat

from config import GSS_FILE, GSS_URL, ITEMS, MIN_UNWEIGHTED_N, SUBGROUPS, WEIGHT

RAW = pathlib.Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
dta = next(RAW.rglob(GSS_FILE), None)
if dta is None:
    print("Downloading GSS 2024 ...")
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(GSS_URL).read()))
    z.extractall(RAW)
    dta = next(RAW.rglob(GSS_FILE))

cols = [WEIGHT, "age", "sex", "degree"] + list(ITEMS)
df, _ = pyreadstat.read_dta(str(dta), usecols=cols)
df = df.apply(pd.to_numeric, errors="coerce")  # GSS lettered missing codes become NaN
df = df[df[WEIGHT].notna() & (df[WEIGHT] > 0)]

rows = []
for g, (_, q) in SUBGROUPS.items():
    sub = df.query(q)
    for var, (domain, _, target, codes) in ITEMS.items():
        d = sub[[var, WEIGHT]].dropna()
        n = len(d)
        if n < MIN_UNWEIGHTED_N:
            continue
        w = d[WEIGHT].to_numpy()
        y = d[var].isin(codes).to_numpy().astype(float)
        p = float(np.sum(w * y) / np.sum(w))
        n_eff = float(w.sum() ** 2 / np.sum(w ** 2))  # Kish effective sample size
        se = float(np.sqrt(p * (1 - p) / n_eff))
        rows.append(dict(item=var, domain=domain, subgroup=g, target=target, n=n,
                         n_eff=round(n_eff, 1), truth_pct=round(100 * p, 2),
                         truth_se_pct=round(100 * se, 2)))

out = pd.DataFrame(rows)
out.to_csv("data/truth.csv", index=False)
excluded = len(ITEMS) * len(SUBGROUPS) - len(out)
print(f"{len(out)} cells written to data/truth.csv ({excluded} excluded below n={MIN_UNWEIGHTED_N})")
