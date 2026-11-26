"""Readiness score, Final v1.1 (questions renumbered I01-I12 in gate order, 24 Nov 2026).

Scoring rules (paper, Section V-F):
- A gate is met when every question in it is Yes or N/A.
- Level = number of consecutive gates met, counting from G1 (0-4).
- Blocking question = first No in the first unmet gate.
- Coverage = Yes / applicable questions (for comparison only; it does not change the level).
"""

GATES = {
    "G1": "Registered",
    "G2": "Staff records",
    "G3": "Ongoing duties",
    "G4": "Saudization",
}

LEVEL_NAMES = {
    0: "Not registered",
    1: "Registered",
    2: "Staff on record",
    3: "Ongoing duties met",
    4: "Ready",
}

# id, gate, question, where to check, consequence of No (size C / B / A), N/A allowed when (None = never)
QUESTIONS = [
    ("I01", "G1", "Does my business have a file on Qiwa, with the right address and branches?",
     "Qiwa: establishment profile and branches",
     "Fine 500 / 1,000 / 1,500 SAR (size C / B / A)", None),
    ("I02", "G1", "Is my business registered with GOSI?",
     "GOSI Online: View Establishment Information",
     "No access to GOSI services such as the GOSI certificate; no fine stated",
     "The establishment employs no workers"),
    ("I03", "G2", "Is every employee's contract on Qiwa?",
     "Qiwa: contracts page",
     "Fine 300 / 500 / 1,000 SAR per worker (size C / B / A); a Saudi worker without a documented contract is not counted in Nitaqat",
     "The establishment has no workers"),
    ("I04", "G2", "Is every employee registered with GOSI?",
     "GOSI Online: List of Establishment Contributors",
     "Fines for late or refused registration",
     "No worker meets GOSI coverage conditions"),
    ("I05", "G2", "Is each employee's salary entered correctly in GOSI?",
     "GOSI Online: annual wages; subscriber wage details",
     "Penalties for missing, late, or wrong wage data",
     "No worker is registered with GOSI"),
    ("I06", "G2", "Is every Saudi on my GOSI list really working for me?",
     "GOSI Online: List of Establishment Contributors, compared with actual staff",
     "Fine 5,000 / 8,000 / 15,000 SAR per person (size C / B / A)",
     "No Saudi worker is registered"),
    ("I07", "G2", "Do my business and every employee have a bank account?",
     "Mudad: bank details",
     "Wage file cannot be uploaded, or bank processing fails; WPS violations are recorded",
     "Not subject to the Wage Protection Program"),
    ("I08", "G2", "Is the person who uploads salaries registered with the Ministry as a Mudad user?",
     "Mudad: users",
     "That person cannot upload wage files",
     "Not subject to the Wage Protection Program"),
    ("I09", "G3", "Did I upload the salary file to Mudad every month, at the compliance rate the Ministry sets?",
     "Mudad: wage protection dashboard and compliance rate",
     "Fine 500 / 1,000 / 2,000 SAR (size C / B / A)",
     "Not subject to the Wage Protection Program"),
    ("I10", "G3", "Have I paid all my GOSI bills on time?",
     "GOSI Online: View establishment bill (paid through SADAD)",
     "2% of the amount due for each month of delay",
     "No registered contributors"),
    ("I11", "G3", "Do I let GOSI inspectors see my work, staff, and salary records?",
     "My own records; GOSI inspection notices",
     "Fine up to 50,000 SAR, doubled if repeated", None),
    ("I12", "G4", "Do I have enough Saudi employees for my business type?",
     "Qiwa: Nitaqat page",
     "Fine 2,000 / 4,000 / 6,000 SAR (size C / B / A) for each non-Saudi worker above the ratio",
     "No Saudization decision covers the activity"),
]

ANSWERS = ("Yes", "No", "N/A")


def score(answers):
    """answers: dict id -> 'Yes' / 'No' / 'N/A'. Returns a result dict."""
    missing = [q[0] for q in QUESTIONS if answers.get(q[0]) not in ANSWERS]
    if missing:
        return {"status": "Incomplete", "missing": missing}
    bad_na = [q[0] for q in QUESTIONS if q[5] is None and answers[q[0]] == "N/A"]
    if bad_na:
        return {"status": "Check answers", "bad_na": bad_na}

    gate_met = {}
    for g in GATES:
        gate_met[g] = all(answers[q[0]] in ("Yes", "N/A") for q in QUESTIONS if q[1] == g)

    level = 0
    for g in GATES:
        if not gate_met[g]:
            break
        level += 1

    blocking = None
    if level < 4:
        first_unmet = list(GATES)[level]
        for q in QUESTIONS:
            if q[1] == first_unmet and answers[q[0]] == "No":
                blocking = q
                break

    applicable = [q for q in QUESTIONS if answers[q[0]] != "N/A"]
    yes = sum(answers[q[0]] == "Yes" for q in applicable)
    coverage = yes / len(applicable) if applicable else 0.0
    open_items = [q[0] for q in QUESTIONS if answers[q[0]] == "No"]

    return {"status": "OK", "level": level, "level_name": LEVEL_NAMES[level],
            "gate_met": gate_met, "blocking": blocking, "coverage": coverage,
            "open_items": open_items}


# Illustrative cafe (paper, Section VI-C): 8 employees (size C); all Yes except
# contracts on Qiwa (I03) and Saudization (I12).
CAFE_BEFORE = {q[0]: "Yes" for q in QUESTIONS}
CAFE_BEFORE.update({"I03": "No", "I12": "No"})
CAFE_AFTER = dict(CAFE_BEFORE, I03="Yes")
