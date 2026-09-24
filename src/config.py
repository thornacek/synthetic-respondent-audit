"""Frozen study design. Edit only before the seal tag. See PREREGISTRATION.md."""

GSS_URL = "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/2024_stata.zip"
GSS_FILE = "GSS2024.dta"
WEIGHT = "wtssps"          # GSS-recommended person post-stratification weight
MIN_UNWEIGHTED_N = 50      # cells below this base are excluded, not reported
INTERVAL = 0.80            # nominal coverage the model is asked for
RUNS_PER_CELL = 3          # independent calls per cell, fresh context each
MODEL = "claude-haiku-4-5-20251001"
TEMPERATURE = 1.0          # default sampling; run-to-run spread is itself a finding

CON_STEM = ("I am going to name some institutions in this country. As far as the people running "
            "these institutions are concerned, would you say you have a great deal of confidence, "
            "only some confidence, or hardly any confidence at all in them? ")
NAT_STEM = ("We are faced with many problems in this country, none of which can be solved easily "
            "or inexpensively. Are we spending too much, too little, or about the right amount on: ")

# var: (domain, question wording, target answer shown to model, target codes)
ITEMS = {
    "happy":    ("wellbeing", "Taken all together, how would you say things are these days: would you say that you are very happy, pretty happy, or not too happy?", "very happy", [1]),
    "health":   ("wellbeing", "Would you say your own health, in general, is excellent, good, fair, or poor?", "excellent or good", [1, 2]),
    "satfin":   ("wellbeing", "So far as you and your family are concerned, would you say that you are pretty well satisfied with your present financial situation, more or less satisfied, or not satisfied at all?", "pretty well satisfied", [1]),
    "satjob":   ("wellbeing", "On the whole, how satisfied are you with the work you do: very satisfied, moderately satisfied, a little dissatisfied, or very dissatisfied? (asked of people currently working)", "very satisfied", [1]),
    "fear":     ("wellbeing", "Is there any area right around here, that is, within a mile, where you would be afraid to walk alone at night?", "yes", [1]),
    "trust":    ("social_trust", "Generally speaking, would you say that most people can be trusted or that you can't be too careful in dealing with people?", "most people can be trusted", [1]),
    "helpful":  ("social_trust", "Would you say that most of the time people try to be helpful, or that they are mostly just looking out for themselves?", "try to be helpful", [1]),
    "fair":     ("social_trust", "Do you think most people would try to take advantage of you if they got a chance, or would they try to be fair?", "would try to be fair", [2]),
    "getahead": ("social_trust", "Some people say that people get ahead by their own hard work; others say that lucky breaks or help from other people are more important. Which do you think is most important?", "hard work most important", [1]),
    "conbus":   ("institutions", CON_STEM + "Major companies", "a great deal of confidence", [1]),
    "conmedic": ("institutions", CON_STEM + "Medicine", "a great deal of confidence", [1]),
    "consci":   ("institutions", CON_STEM + "Scientific community", "a great deal of confidence", [1]),
    "conpress": ("institutions", CON_STEM + "Press", "a great deal of confidence", [1]),
    "contv":    ("institutions", CON_STEM + "Television", "a great deal of confidence", [1]),
    "confinan": ("institutions", CON_STEM + "Banks and financial institutions", "a great deal of confidence", [1]),
    "coneduc":  ("institutions", CON_STEM + "Education", "a great deal of confidence", [1]),
    "conarmy":  ("institutions", CON_STEM + "Military", "a great deal of confidence", [1]),
    "natsci":   ("spending", NAT_STEM + "Supporting scientific research", "too little", [1]),
    "natenvir": ("spending", NAT_STEM + "Improving and protecting the environment", "too little", [1]),
    "natroad":  ("spending", NAT_STEM + "Highways and bridges", "too little", [1]),
}

# name: (description shown to model, pandas query on GSS columns)
SUBGROUPS = {
    "total":     ("U.S. adults (18 and older)", "age >= 18"),
    "women":     ("U.S. women (18 and older)", "sex == 2"),
    "men":       ("U.S. men (18 and older)", "sex == 1"),
    "age18_34":  ("U.S. adults aged 18 to 34", "age >= 18 and age <= 34"),
    "age55plus": ("U.S. adults aged 55 and older", "age >= 55"),
    "ba_plus":   ("U.S. adults with a bachelor's degree or higher", "degree >= 3"),
}

PROMPT = """You are estimating results from a nationally representative probability survey of U.S. adults, fielded in 2024.

Population: {population}
Question as asked: "{question}"

Estimate the percentage of this population who answered: "{target}" (among those who gave a valid answer).

Give your best estimate and an {pct}% interval: a range you believe has an {pct}% chance of containing the true survey result.

Respond with JSON only, no other text: {{"estimate": <number>, "low": <number>, "high": <number>}}. All values are percentages from 0 to 100."""
