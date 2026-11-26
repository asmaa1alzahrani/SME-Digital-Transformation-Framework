import streamlit as st
from html import escape
from readiness import (
    ANSWERS, CAFE_AFTER, CAFE_BEFORE,
    GATES, QUESTIONS, score
)

st.set_page_config(
    page_title="SME Compliance Readiness",
    page_icon="📋",
    layout="wide"
)

# =========================
# Dashboard styling
# =========================

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FA;
}
.block-container {
    padding-top: 2rem;
    max-width: 1450px;
}
[data-testid="stSidebar"] {
    background-color: #E8EFF3;
}
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #DCE5EB;
    border-radius: 12px;
    padding: 18px;
    min-height: 120px;
}
[data-testid="stMetricValue"] {
    color: #176B65;
}
[data-testid="stExpander"] {
    background: white;
    border-radius: 10px;
}
.hero {
    background: linear-gradient(120deg, #123D46, #176B65);
    padding: 30px;
    border-radius: 16px;
    margin-bottom: 24px;
    color: white;
}
.hero h1 {
    color: white;
    font-size: 32px;
    margin: 0;
}
.hero p {
    color: #DCEBEA;
    margin: 8px 0;
}
.gate-card {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    border-left: 5px solid;
}

.hero {
    padding: 18px 24px;
    margin-bottom: 12px;
}
.hero h1 {
    font-size: 28px;
}
.hero p {
    margin: 4px 0;
}
[data-testid="stMetric"] {
    min-height: 90px;
    padding: 12px;
}
button[kind="primary"] {
    background-color: #176B65 !important;
    border-color: #176B65 !important;
    color: white !important;
}
[data-testid="stProgress"] div[role="progressbar"] > div {
    background-color: #176B65 !important;
}
[data-testid="stRadio"] input {
    accent-color: #176B65;
}
.gate-card {
    padding: 10px 14px;
    margin-bottom: 6px;
}
[data-testid="stMarkdownContainer"] hr {
    margin: 12px 0;
}

</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================

st.markdown("""
<div class="hero">
    <h1>SME Compliance Readiness Assessment</h1>
    <p>Compliance-Driven Digital Transformation
    Framework for Saudi SMEs</p>
    <p style="font-size:13px;">
        Research Prototype | Version 1.2
    </p>
</div>
""", unsafe_allow_html=True)

# =========================
# Sidebar and presets
# =========================

PRESETS = {
    "Blank assessment": {},
    "Café — Before improvement": CAFE_BEFORE,
    "Café — After improvement": CAFE_AFTER
}

with st.sidebar:
    st.title("Assessment Settings")

    st.markdown("### Example Scenarios")

    preset = st.selectbox(
        "Select an assessment",
        list(PRESETS)
    )

    if st.button(
        "Apply scenario",
        use_container_width=True,
        type="primary"
    ):
        for q in QUESTIONS:
            st.session_state[q[0]] = PRESETS[preset].get(q[0])

    if st.button(
        "Reset assessment",
        use_container_width=True
    ):
        for q in QUESTIONS:
            st.session_state[q[0]] = None

    st.divider()

    st.markdown("### Readiness Levels")

    levels = {
        0: "Not registered",
        1: "Registered",
        2: "Staff on record",
        3: "Ongoing duties met",
        4: "Ready"
    }

    for level, name in levels.items():
        st.markdown(f"**Level {level}** — {name}")

    st.divider()

    st.caption(
        "This research prototype uses self-reported "
        "answers and does not connect to government platforms."
    )

# =========================
# Main layout
# =========================

left, right = st.columns([1.15, 1], gap="large")

answers = {}

# =========================
# Questionnaire
# =========================

with left:

    st.subheader("Compliance Questionnaire")

    progress_area = st.empty()

    st.caption(
        "Answer each indicator according to your "
        "establishment's current status."
    )

    for g, gname in GATES.items():

        gate_questions = [
            q for q in QUESTIONS if q[1] == g
        ]

        with st.expander(
            f"{g} — {gname} | "
            f"{len(gate_questions)} indicators",
            expanded=(g == "G1")
        ):

            for qid, gate, text, where, cons, na_rule in gate_questions:

                options = ANSWERS if na_rule else ("Yes", "No")

                help_text = (
                    f"Where to check: {where}. "
                    f"N/A only if: {na_rule or 'never'}."
                )

                answers[qid] = st.radio(
                    f"{qid}. {text}",
                    options,
                    index=None,
                    horizontal=True,
                    key=qid,
                    help=help_text
                )

                if answers[qid] == "N/A":
                    st.caption(
                        f"N/A condition: {na_rule}"
                    )

    answered = sum(
        value in ANSWERS
        for value in answers.values()
    )

    with progress_area.container():
        st.progress(answered / len(QUESTIONS))
        st.caption(
            f"{answered} of {len(QUESTIONS)} indicators answered"
        )

# =========================
# Original scoring function
# =========================

res = score(answers)

# =========================
# Assessment results
# =========================

with right:

    st.subheader("Assessment Overview")

    if res["status"] == "Incomplete":

        st.info(
            f"Complete the remaining "
            f"{len(res['missing'])} indicator(s) "
            "to view your assessment results."
        )

    elif res["status"] == "Check answers":

        st.error(
            "N/A is not allowed for: "
            + ", ".join(res["bad_na"])
        )

    else:

        # KPI cards

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Readiness Level",
            f"{res['level']} / 4"
        )

        c2.metric(
            "Coverage",
            f"{res['coverage']:.1%}"
        )

        c3.metric(
            "Open Items",
            len(res["open_items"])
        )

        st.markdown(
            f"**Current level:** {res['level_name']}"
        )

        st.divider()

        # Gate visualization

        st.subheader("Readiness Journey")

        for i, (g, name) in enumerate(GATES.items()):

            met = res["gate_met"][g]

            if met:
                color = "#287653"
                background = "#E6F3EB"
                status = "✓ Met"
            else:
                color = "#B45309"
                background = "#FFF3E0"
                status = "Not met"

            st.markdown(f"""
            <div class="gate-card"
                 style="background:{background};
                        border-color:{color};">
                <div style="display:flex;
                            justify-content:space-between;
                            color:#243746;">
                    <strong>{g} — {escape(name)}</strong>
                    <strong style="color:{color};">
                        {status}
                    </strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(
            "Gate status reflects its own indicators. "
            "Readiness counts only consecutive met gates "
            "starting from G1."
        )

        st.divider()

        # Priority blocker

        st.subheader("Priority Action")

        if res["blocking"]:

            qid, gate, text, where, cons, _ = res["blocking"]

            st.warning(
                f"**Blocking requirement: {qid} ({gate})**"
            )

            st.markdown(f"**Requirement:** {text}")

            st.markdown(f"**Where to fix:** {where}")

            st.markdown(f"**Potential consequence:** {cons}")

            st.caption(
                "Regulatory consequences are provided "
                "for reference and should be verified "
                "against current official regulations."
            )

        else:

            st.success(
                "All four readiness gates are met."
            )

        # Open requirements

        if res["open_items"]:

            with st.expander(
                f"All Open Requirements "
                f"({len(res['open_items'])})"
            ):

                for q in QUESTIONS:

                    if q[0] in res["open_items"]:

                        st.markdown(
                            f"**{q[0]} — {q[2]}**"
                        )

                        st.caption(
                            f"Where to fix: {q[3]}"
                        )

                        st.divider()

# =========================
# Footer
# =========================

st.divider()

st.caption(
    "Compliance-Driven Digital Transformation Framework "
    "for Saudi SMEs | Academic Research Prototype"
)
