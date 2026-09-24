# Pre-registration

Committed and tagged `seal-v1` before any model call. The tag's commit must precede the first commit of `data/estimates.jsonl`. Anyone can check this with `git log --follow data/estimates.jsonl` against `git show seal-v1`.

## Question
When an LLM stands in for survey respondents, how accurate are its estimates of real survey results, and how honest are its stated uncertainty ranges?

## Ground truth
- General Social Survey 2024, NORC at the University of Chicago. Weighted with `wtssps` (GSS-recommended person post-stratification weight). Cases without a weight are excluded.
- Each item is recoded to one target answer ("top box"), fixed in `src/config.py`. The percentage is among valid answers only. Don't know, refused, and not-asked are excluded.
- Truth uncertainty is reported as a standard error using Kish effective sample size.

## Design
- 20 items across four domains: wellbeing, social trust, confidence in institutions, and public spending priorities.
- 6 subgroups: total, women, men, 18 to 34, 55 and older, bachelor's degree or higher.
- 120 cells. Cells with an unweighted base under 50 are excluded before any model call. None fell below that line.
- Model: `claude-haiku-4-5-20251001` at default temperature. 3 independent calls per cell, each a fresh context.
- The prompt is fixed in `src/config.py`. It gives the question wording and the population, and asks for a point estimate and an 80% interval. It does not name the survey.

## Metrics
1. **Primary: interval coverage.** The share of cells where the truth falls inside the model's 80% interval. It uses run 1 only, so there is one independent observation per cell, and it's reported with a 95% Wilson interval. The benchmark is 80%.
2. Mean and median absolute error, with the estimate averaged across the 3 runs. Mean signed error, to test whether the model systematically overstates top-box answers relative to real respondents.
3. Mean interval width, and run-to-run standard deviation (consistency).
4. **Error drivers.** An exact Shapley decomposition of R² from an OLS regression of absolute error. The predictor groups are topic domain, subgroup, log effective base size, and how lopsided the true answer is (distance from 50%). The groups are correlated, especially subgroup and base size. Shapley assigns shared variance evenly, which is why it's used here.

## Known limits, stated in advance
- **Contamination.** GSS results are public, and the model may have seen published toplines. Subgroup cells are rarely published, so they are the cleaner test. Results are reported for total and subgroup cells separately.
- 120 cells from one survey and one model. No claims beyond this design.
- Top-box recodes are one reasonable choice among several.
- Nothing here measures whether synthetic respondents are useful for any specific business decision. It measures accuracy and honesty on known answers.

## Amendments
Any change after `seal-v1` gets a new tag (`seal-v2`), a dated entry here with its motivation, and a full re-run. No edits to fit results.
