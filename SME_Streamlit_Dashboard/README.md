# SME Compliance Intelligence — Streamlit Prototype

A Streamlit + Plotly dashboard for the team's 12-indicator, 4-gate readiness assessment.
Uses the original `score()` implementation in `readiness.py`, with the team's CSVs.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Colab
Open `Launch_SME_Streamlit_in_Colab.ipynb`, upload `SME_Streamlit_Dashboard.zip` when prompted, and run the cells in order. The last cell opens the Streamlit app using Colab's port proxy.

## Tabs
- Overview: KPI cards, gate statuses, unmet requirements, priority blocker.
- SME Assessment: all 12 questions, original N/A restrictions, downloadable answers, what-if re-assessment.
- Dependencies: 17 evidence-linked rows and question catalogue.
- Evaluation Lab: precomputed original A4/A6/A7 outputs.

## Research limits
Synthetic example only. The assessment logic is implemented, but regulatory accuracy, evidence links, N/A eligibility and real-world effectiveness are not independently verified. This is not legal advice or a live integration with government systems.
