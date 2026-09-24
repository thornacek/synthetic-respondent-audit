# Seal checklist (delete after the run)

1. `python src/prepare_truth.py` and confirm 120 cells.
2. Read the prompt in `src/config.py` once more. After the seal it's frozen.
3. `git add -A && git status` and confirm no key, no `.env`, no `data/raw/`.
4. `git commit -m "Pre-registration: design, prompt, truth" && git tag seal-v1 && git push --tags`
5. `python src/run_model.py`, then `git add data/estimates.jsonl && git commit -m "Raw model outputs"`
6. `python src/score.py`, then commit `results/`.
7. Fill the README Results section with the real numbers and charts. Push.
