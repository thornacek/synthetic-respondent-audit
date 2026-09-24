"""Ask the model for each cell, fresh context per call. Resumable.

Usage:
  python src/run_model.py          real run (needs ANTHROPIC_API_KEY in the environment)
  python src/run_model.py --mock   pipeline test only; writes a MOCK file that is never published
"""
import datetime
import json
import pathlib
import random
import re
import sys

import pandas as pd

from config import INTERVAL, ITEMS, MODEL, PROMPT, RUNS_PER_CELL, SUBGROUPS, TEMPERATURE

MOCK = "--mock" in sys.argv
out_path = pathlib.Path("data/estimates_MOCK.jsonl" if MOCK else "data/estimates.jsonl")
truth = pd.read_csv("data/truth.csv")

done = set()
if out_path.exists():
    for line in out_path.read_text().splitlines():
        r = json.loads(line)
        done.add((r["item"], r["subgroup"], r["run"]))

if not MOCK:
    import anthropic
    client = anthropic.Anthropic()  # key comes from the environment; never hard-code it


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    try:
        j = json.loads(m.group(0))
        return {k: float(j[k]) for k in ("estimate", "low", "high")}
    except Exception:
        return None  # counted as a parse failure in scoring, never silently dropped


rng = random.Random(20260923)  # mock only
with out_path.open("a") as f:
    for _, c in truth.iterrows():
        _, question, target, _ = ITEMS[c["item"]]
        prompt = PROMPT.format(population=SUBGROUPS[c["subgroup"]][0], question=question,
                               target=target, pct=int(INTERVAL * 100))
        for run in range(1, RUNS_PER_CELL + 1):
            if (c["item"], c["subgroup"], run) in done:
                continue
            if MOCK:
                est = c["truth_pct"] + rng.gauss(0, 8)
                half = rng.uniform(4, 12)
                raw = json.dumps({"estimate": est, "low": est - half, "high": est + half})
                model = "MOCK"
            else:
                msg = client.messages.create(model=MODEL, max_tokens=200, temperature=TEMPERATURE,
                                             messages=[{"role": "user", "content": prompt}])
                raw, model = msg.content[0].text, msg.model
            rec = dict(item=c["item"], subgroup=c["subgroup"], run=run, model=model, raw=raw,
                       parsed=parse(raw),
                       ts=datetime.datetime.now(datetime.timezone.utc).isoformat())
            f.write(json.dumps(rec) + "\n")
            f.flush()
print(f"Done. Estimates in {out_path}")
