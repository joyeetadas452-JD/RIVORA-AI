import streamlit as st

from core.risk_engine import RiskInput, assess_risk


st.set_page_config(
    page_title="RIVORA AI",
    page_icon="🌊",
    layout="wide"
)


# ---------- HEADER ----------
st.title("🌊 RIVORA AI")
st.subheader("AI-Powered Community Flood Risk & Preparedness Assistant")

st.markdown(
    """
    RIVORA AI helps communities interpret environmental and
    community-level flood and waterlogging risk factors and provides
    understandable preparedness guidance.
    """
)

st.info(
    "⚠️ This is an AI-assisted relative risk assessment, not an official "
    "flood warning. Always follow instructions from authorized government "
    "and disaster-management agencies."
)


# ---------- SIDEBAR ----------
st.sidebar.title("RIVORA AI")
page = st.sidebar.radio(
    "Choose a section",
    ["Main", "Risk Assessment", "Preparedness Assistant", "Evidence"]
)


# ---------- MAIN ----------
if page == "Main":

    st.header("Community Flood Risk & Preparedness")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Primary SDG", "SDG 11")

    with col2:
        st.metric("Secondary SDGs", "SDG 13 & SDG 6")

    with col3:
        st.metric("Risk Levels", "5")

    st.markdown("---")

    st.subheader("How RIVORA AI Works")

    st.markdown(
        """
        **Environmental & community inputs**
        ↓

        **Deterministic flood-risk assessment**
        ↓

        **Explainable risk classification**
        ↓

        **Preparedness guidance**
        ↓

        **Community decision support**
        """
    )

    st.warning(
        "The system does not invent missing environmental information. "
        "If important information is unavailable, it reports "
        "'INSUFFICIENT DATA'."
    )


# ---------- RISK ASSESSMENT ----------
elif page == "Risk Assessment":

    st.header("🌧️ Flood Risk Assessment")

    st.write(
        "Enter the available environmental and community conditions."
    )

    col1, col2 = st.columns(2)

    with col1:

        rainfall_intensity = st.selectbox(
            "Rainfall intensity",
            [
                "Light",
                "Moderate",
                "Heavy",
                "Very Heavy",
                "Unknown"
            ]
        )

        rainfall_duration = st.number_input(
            "Rainfall duration (hours)",
            min_value=0.0,
            max_value=72.0,
            value=1.0,
            step=0.5
        )

        drainage = st.selectbox(
            "Drainage condition",
            [
                "Good",
                "Moderate",
                "Poor",
                "Unknown"
            ]
        )

    with col2:

        terrain = st.selectbox(
            "Terrain / elevation",
            [
                "Elevated",
                "Normal",
                "Low-lying",
                "Unknown"
            ]
        )

        previous_flooding = st.selectbox(
            "Previous flooding",
            [
                "None",
                "Occasional",
                "Frequent",
                "Unknown"
            ]
        )

        water_accumulation = st.selectbox(
            "Existing water accumulation",
            [
                "None",
                "Minor",
                "Moderate",
                "Significant",
                "Unknown"
            ]
        )

    st.markdown("---")

    if st.button("🔍 Assess Flood Risk", type="primary"):

        risk_input = RiskInput(
            rainfall_intensity=rainfall_intensity,
            rainfall_duration_hours=rainfall_duration,
            drainage=drainage,
            terrain=terrain,
            previous_flooding=previous_flooding,
            water_accumulation=water_accumulation
        )

        result = assess_risk(risk_input)

        st.subheader("Risk Assessment Result")

        level = result.level

        if level == "LOW":
            st.success(f"🟢 Risk Level: {level}")

        elif level == "MODERATE":
            st.warning(f"🟡 Risk Level: {level}")

        elif level == "HIGH":
            st.error(f"🟠 Risk Level: {level}")

        elif level == "VERY HIGH":
            st.error(f"🔴 Risk Level: {level}")

        else:
            st.info(f"⚪ Risk Level: {level}")

        st.write(f"**Risk Score:** {result.score}")

        st.subheader("Why this risk level?")

        for factor in result.factors:
            st.write(f"• {factor}")

        st.write(result.explanation)

        st.subheader("Uncertainty & Safety")

        st.info(result.uncertainty)

        st.subheader("Recommended Preparedness Actions")

        st.markdown(
            """
            **Before flooding**
            - Monitor official weather and disaster-management information.
            - Keep important documents and essential items protected.
            - Prepare basic emergency supplies.
            - Know safer routes and designated emergency locations where applicable.

            **During flooding**
            - Avoid unnecessary travel through flooded roads.
            - Do not enter fast-moving or unknown-depth water.
            - Stay away from electrical hazards.
            - Follow official evacuation instructions.

            **After flooding**
            - Follow official guidance before returning to affected areas.
            - Avoid potentially contaminated floodwater.
            - Be careful around damaged roads, buildings and electrical infrastructure.
            - Report hazards to the appropriate authorities.
            """
        )


# ---------- PREPAREDNESS ----------
elif page == "Preparedness Assistant":

    st.header("🛟 Preparedness Assistant")

    st.write(
        "General flood preparedness guidance for community members."
    )

    question = st.text_input(
        "Ask a preparedness question",
        placeholder="Example: What should I do during road flooding?"
    )

    if question:

        q = question.lower()

        if "during" in q or "road" in q or "travel" in q:
            st.warning(
                "Avoid unnecessary travel through flooded roads. "
                "Never enter fast-moving or unknown-depth water and "
                "follow official instructions."
            )

        elif "before" in q or "prepare" in q:
            st.info(
                "Monitor official information, protect important documents, "
                "prepare essential supplies and identify safer routes."
            )

        elif "after" in q:
            st.info(
                "Follow official guidance before returning. Avoid contaminated "
                "water and be cautious around damaged infrastructure and electricity."
            )

        else:
            st.info(
                "For safety-critical situations, follow instructions from "
                "authorized disaster-management and government agencies."
            )


# ---------- EVIDENCE ----------
elif page == "Evidence":

    st.header("📚 Evidence & Knowledge Base")

    st.write(
        "RIVORA AI is designed to use reliable flood-preparedness "
        "and disaster-management information as supporting knowledge."
    )

    st.markdown(
        """
        ### Knowledge areas

        - Flood and waterlogging fundamentals
        - Rainfall and drainage factors
        - Community preparedness
        - Rural and agricultural impacts
        - River-related hazards and erosion
        - Emergency preparedness
        - Responsible AI and uncertainty

        ### Responsible use

        RIVORA AI should not invent rainfall measurements, official
        warnings, evacuation orders or local government instructions.

        Official disaster-management authorities remain the authoritative
        source for warnings and emergency instructions.
        """
    )

    st.success("Evidence and safety principles are included in the prototype.")