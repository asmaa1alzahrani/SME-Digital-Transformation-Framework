"""
Readiness score of the Compliance-Driven Digital Transformation Framework
for Saudi SMEs (Final v1.1, 18 Nov 2026) - core scoring logic.

Recreates the Assessment sheet of the Readiness Assessment workbook:
  - 12 questions (questions.csv), each answered "Yes", "No" or "N/A"
  - 4 ordered gates: G1 Registered, G2 Staff records, G3 Ongoing duties, G4 Saudization
  - Level = number of consecutive gates met, counting from G1 (0-4)
  - A gate is met when every question in it is "Yes" or "N/A"

Run:  python readiness.py            (scores the example SME in example_sme.csv)
"""
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent / "data"
GATES = ["G1", "G2", "G3", "G4"]
LEVEL_NAMES = {0: "Not registered", 1: "Registered", 2: "Staff on record",
               3: "Ongoing duties met", 4: "Ready"}
VALID = {"Yes", "No", "N/A"}


def load_questions(path=HERE / "questions.csv") -> pd.DataFrame:
    """The 12 questions, in gate order, with evidence and N/A rules."""
    return pd.read_csv(path).sort_values("order").set_index("id")


def score(answers: dict, questions: pd.DataFrame) -> dict:
    """Score one SME. `answers` maps question id -> "Yes" / "No" / "N/A"."""
    # 1. Validity: every question answered with an allowed value
    missing = [q for q in questions.index if answers.get(q) not in VALID]
    if missing:
        return {"status": "Incomplete", "level": None,
                "message": f"{len(missing)} question(s) not answered: {', '.join(missing)}"}
    # 2. N/A is not allowed where the record applies to every establishment/employer
    bad_na = [q for q in questions.index
              if questions.at[q, "na_never"] == 1 and answers[q] == "N/A"]
    if bad_na:
        return {"status": "Check answers", "level": None,
                "message": f"N/A not allowed for: {', '.join(bad_na)}"}

    # 3. Gate status: met when every answer in the gate is Yes or N/A
    gate_met = {}
    for g in GATES:
        ids = questions.index[questions["gate"] == g]
        gate_met[g] = all(answers[q] in ("Yes", "N/A") for q in ids)

    # 4. Level = consecutive gates met from G1 (non-compensatory)
    level = 0
    for g in GATES:
        if not gate_met[g]:
            break
        level += 1

    # 5. Blocking question = first unmet question in the first unmet gate
    blocking = None
    if level < 4:
        first_gate = GATES[level]
        for q in questions.index[questions["gate"] == first_gate]:
            if answers[q] == "No":
                blocking = q
                break

    # 6. Coverage = Yes / applicable (comparison only; does not set the level)
    applicable = sum(a != "N/A" for a in answers.values())
    yes = sum(a == "Yes" for a in answers.values())
    coverage = yes / applicable if applicable else None

    return {
        "status": "OK",
        "level": level,
        "level_name": LEVEL_NAMES[level],
        "gate_met": gate_met,
        "blocking_id": blocking,
        "blocking_question": questions.at[blocking, "question"] if blocking else "None",
        "where_to_fix": questions.at[blocking, "where_to_check"] if blocking else "",
        "if_no": questions.at[blocking, "if_no"] if blocking else "",
        "evidence": questions.at[blocking, "records"] if blocking else "",
        "coverage": coverage,
        "open_items": [q for q, a in answers.items() if a == "No"],
    }


def dma_style_band(coverage: float) -> str:
    """Comparator: EU DMA-style banding of an averaged 0-100% score
    (Basic 0-25, Average 26-50, Moderately advanced 51-75, Advanced 76-100).
    Applied to coverage only to contrast averaging with gating."""
    pct = coverage * 100
    if pct <= 25:
        return "Basic"
    if pct <= 50:
        return "Average"
    if pct <= 75:
        return "Moderately advanced"
    return "Advanced"


def report(name: str, answers: dict, questions: pd.DataFrame) -> str:
    r = score(answers, questions)
    if r["status"] != "OK":
        return f"{name}: {r['status']} - {r['message']}"
    lines = [
        f"SME: {name}",
        f"Readiness level: {r['level']} ({r['level_name']})",
        "Gates: " + ", ".join(f"{g} {'met' if m else 'NOT met'}" for g, m in r["gate_met"].items()),
        f"Blocking question: {r['blocking_question']}",
        f"Where to fix it:   {r['where_to_fix']}",
        f"If left:           {r['if_no']}",
        f"Evidence:          {r['evidence']}",
        f"Coverage:          {r['coverage']:.0%}  (DMA-style band: {dma_style_band(r['coverage'])})",
        f"Open items (No):   {', '.join(r['open_items']) or 'none'}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    qs = load_questions()
    ex = pd.read_csv(HERE / "example_sme.csv").set_index("id")["answer"].to_dict()
    text = report("Example: new micro café (synthetic, 8 workers, size C)", ex, qs)
    print(text)
    (HERE / "output").mkdir(exist_ok=True)
    (HERE / "output" / "example_report.txt").write_text(text, encoding="utf-8")
