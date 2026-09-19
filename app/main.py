from datetime import datetime, timedelta
import html
import json
from collections import Counter

import streamlit as st

from core.environmental_domains import DOMAIN_PROFILES, SEVERITY_OPTIONS, assess_domain
from core.open_meteo import (
    LocationNotFoundError,
    OpenMeteoUnavailableError,
    RainfallDataMissingError,
    fetch_recent_rainfall,
    optional_weather_field,
)
from core.risk_engine import RiskInput, assess_risk


RISK_DOMAINS = {
    "Flood & Waterlogging": {
        "status": "Validated prototype",
        "summary": "Deterministic relative assessment with Open-Meteo rainfall reference data.",
        "source": "Risk engine + Open-Meteo reference weather",
        "fields": ["Rainfall intensity", "Rainfall duration", "Terrain / elevation", "Drainage condition"],
    },
    "River & Erosion": {
        "status": "Prototype assessment",
        "summary": "Structured review of river proximity, observed erosion and bank condition.",
        "source": "Manual community inputs; data integration planned",
        "fields": ["River proximity", "Observed erosion", "Bank condition", "Exposure context"],
    },
    "Heat Risk": {
        "status": "Prototype assessment",
        "summary": "Structured review of heat exposure, duration, urban conditions and vulnerability context.",
        "source": "Manual community inputs; data integration planned",
        "fields": list(DOMAIN_PROFILES["Heat Risk"]["fields"]),
    },
    "Air Pollution": {
        "status": "Data integration planned",
        "summary": "Prepared for AQI or air-quality inputs and exposure context when validated data is available.",
        "source": "No live air-quality data connected",
        "fields": list(DOMAIN_PROFILES["Air Pollution"]["fields"]),
    },
    "Water Security": {
        "status": "Prototype assessment",
        "summary": "Structured review of availability, reliability, contamination concern and water stress.",
        "source": "Manual community inputs; data integration planned",
        "fields": ["Availability", "Reliability", "Contamination concern", "Drought / water stress"],
    },
    "Agriculture & Environmental Stress": {
        "status": "Prototype assessment",
        "summary": "Structured review of rainfall or waterlogging, soil condition and crop exposure context.",
        "source": "Manual community inputs; data integration planned",
        "fields": list(DOMAIN_PROFILES["Agriculture & Environmental Stress"]["fields"]),
    },
    "Waste & Environmental Concerns": {
        "status": "Prototype assessment",
        "summary": "Structured review of waste accumulation, drainage blockage and plastic exposure.",
        "source": "Manual community inputs; data integration planned",
        "fields": list(DOMAIN_PROFILES["Waste & Environmental Concerns"]["fields"]),
    },
}


st.set_page_config(
    page_title="RIVORA AI | Environmental Risk & Resilience Intelligence",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root {
            --navy: #0B1220; --surface: #172033; --raised: #1D2A40;
            --text: #F5F7FA; --muted: #AAB5C5; --teal: #19B5A5;
            --teal-soft: #7DD3C7; --warning: #F2B84B; --danger: #E56B6F;
            --line: rgba(170, 181, 197, 0.18);
        }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        .stApp { background: var(--navy); color: var(--text); }
        [data-testid="stHeader"] { background: rgba(11, 18, 32, 0.88); }
        [data-testid="stSidebar"] { background: #0D1728; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding: 2rem 1.2rem; }
        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebar"] * { color: var(--text); }
        [data-testid="stSidebar"] .stRadio label { color: var(--muted); }
        [data-testid="stSidebar"] .stRadio label:hover { color: var(--teal-soft); }
        .block-container { max-width: 1180px; padding: 3rem 3rem 5rem; }
        h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; color: var(--text); }
        h1 { font-size: clamp(2.2rem, 5vw, 4.8rem); line-height: 1.02; margin: 0; }
        h2 { font-size: clamp(1.6rem, 3vw, 2.35rem); margin-top: 0.2rem; }
        p, li, label, .stMarkdown { color: var(--muted); }
        .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted); }
        .stTextInput input, .stNumberInput input, [data-baseweb="select"] > div { background: #101A2B; color: var(--text); border: 1px solid var(--line); border-radius: 6px; }
        .stTextInput input:focus, .stNumberInput input:focus { border-color: var(--teal); box-shadow: 0 0 0 1px var(--teal); }
        .stButton > button { border-radius: 6px; border: 1px solid var(--line); background: #1B2940; color: var(--text); font-weight: 600; min-height: 2.65rem; }
        .stButton > button:hover { border-color: var(--teal); color: var(--teal-soft); }
        .stButton > button[kind="primary"] { background: var(--teal); border-color: var(--teal); color: #08151B; }
        .stButton > button[kind="primary"]:hover { background: var(--teal-soft); color: #08151B; }
        [data-testid="stAlert"] { border-radius: 6px; border: 1px solid var(--line); background: #142238; }
        hr { border-color: var(--line); margin: 2.5rem 0; }
        .brand-lockup { padding: 0.3rem 0 2rem; }
        .brand-name { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; letter-spacing: 0.08em; }
        .brand-subtitle { color: var(--muted); font-size: 0.72rem; line-height: 1.4; margin-top: 0.45rem; }
        .status-line { color: var(--teal-soft); font-size: 0.72rem; margin-top: 1.1rem; }
        .eyebrow, .section-kicker, .surface-label, .risk-label { color: var(--teal-soft); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
        .page-subtitle { color: var(--muted); font-size: 1.05rem; margin: 0.6rem 0 2.2rem; max-width: 680px; }
        .hero-copy { color: var(--muted); font-size: 1.1rem; line-height: 1.7; max-width: 670px; margin: 1.5rem 0 0; }
        .surface { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 1.35rem; height: 100%; }
        .surface-tight { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 1rem 1.15rem; height: 100%; }
        .surface-title { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.12rem; font-weight: 600; margin: 0.75rem 0 0.4rem; }
        .surface-copy { color: var(--muted); font-size: 0.9rem; line-height: 1.55; }
        .flow-arrow { color: var(--teal); font-size: 1.5rem; text-align: center; padding-top: 2rem; }
        .sdg-number { color: var(--teal-soft); font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; }
        .sdg-label { color: var(--muted); font-size: 0.82rem; }
        .safety-panel { border-left: 3px solid var(--teal); background: rgba(25, 181, 165, 0.08); padding: 1rem 1.2rem; color: var(--muted); line-height: 1.55; }
        .section-kicker { margin: 1.6rem 0 0.8rem; }
        .risk-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 1.8rem; }
        .risk-panel.low { border-top: 3px solid var(--teal); }
        .risk-panel.moderate { border-top: 3px solid var(--warning); }
        .risk-panel.high, .risk-panel.very-high { border-top: 3px solid var(--danger); }
        .risk-panel.insufficient-data { border-top: 3px solid var(--muted); }
        .risk-meta { color: var(--muted); font-size: 0.88rem; line-height: 1.6; margin-top: 0.9rem; }
        .risk-level { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 2.8rem; font-weight: 700; margin-top: 0.45rem; }
        .score-label { color: var(--muted); font-size: 0.8rem; margin-top: 1.1rem; }
        .score-value { color: var(--teal-soft); font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 600; }
        .gauge-track { background: #0F1A2B; border: 1px solid var(--line); border-radius: 99px; height: 0.65rem; margin: 0.8rem 0 0.35rem; overflow: hidden; }
        .gauge-fill { background: var(--teal); border-radius: 99px; height: 100%; }
        .gauge-scale { color: var(--muted); display: flex; font-size: 0.7rem; justify-content: space-between; }
        .status-row { display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 0.6rem 0 0.1rem; }
        .status-chip { background: #101A2B; border: 1px solid var(--line); border-radius: 99px; color: var(--muted); font-size: 0.76rem; padding: 0.45rem 0.7rem; }
        .status-chip strong { color: var(--teal-soft); font-weight: 600; }
        .driver-bar { background: #0F1A2B; border-radius: 99px; height: 0.42rem; margin: 0.3rem 0 0.7rem; overflow: hidden; }
        .driver-fill { background: var(--teal); border-radius: 99px; height: 100%; }
        .metric-value { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 600; }
        .map-note { color: var(--muted); font-size: 0.76rem; margin-top: 0.5rem; }
        .history-row { border-bottom: 1px solid var(--line); color: var(--muted); display: grid; font-size: 0.8rem; grid-template-columns: 1.25fr 1.3fr 0.8fr 0.5fr; gap: 0.5rem; padding: 0.65rem 0; }
        .history-row strong { color: var(--text); font-weight: 600; }
        .compare-value { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.55rem; font-weight: 600; }
        .delta-note { color: var(--teal-soft); font-size: 0.8rem; margin-top: 0.4rem; }
        .analytics-note { color: var(--muted); font-size: 0.8rem; line-height: 1.5; }
        .empty-state { border: 1px dashed var(--line); color: var(--muted); padding: 2rem 1.3rem; text-align: center; }
        .factor-row { align-items: center; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; padding: 0.75rem 0; }
        .factor-row:last-child { border-bottom: 0; }
        .factor-name { color: var(--muted); font-size: 0.9rem; }
        .factor-score { color: var(--text); font-weight: 700; }
        .action-title { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; }
        .action-list { color: var(--muted); font-size: 0.88rem; line-height: 1.65; margin: 0.65rem 0 0; padding-left: 1.1rem; }
        .prompt-note { color: var(--muted); font-size: 0.83rem; margin: 0.25rem 0 1rem; }
        .evidence-index { color: var(--teal-soft); font-family: 'Space Grotesk', sans-serif; font-size: 0.85rem; }
        .command-shell { background: linear-gradient(135deg, #101d2f 0%, #0d1727 62%, #12283a 100%); border: 1px solid rgba(125, 211, 199, 0.24); border-radius: 10px; padding: 1.5rem; margin-bottom: 1.2rem; box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22); }
        .command-title { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: clamp(1.7rem, 3vw, 2.7rem); font-weight: 700; line-height: 1.05; margin: 0.35rem 0 0.5rem; }
        .command-subtitle { color: var(--muted); font-size: 0.94rem; line-height: 1.55; max-width: 760px; }
        .command-meta { color: var(--teal-soft); font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; }
        .kpi-strip { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 0.65rem; margin: 1rem 0 1.15rem; }
        .kpi-card { background: #142338; border: 1px solid var(--line); border-radius: 7px; min-height: 86px; padding: 0.8rem 0.85rem; }
        .kpi-card .surface-label { font-size: 0.62rem; letter-spacing: 0.1em; }
        .kpi-value { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; margin-top: 0.45rem; overflow-wrap: anywhere; }
        .kpi-context { color: var(--muted); font-size: 0.68rem; margin-top: 0.2rem; }
        .workspace-label { color: var(--teal-soft); font-size: 0.7rem; font-weight: 700; letter-spacing: 0.13em; margin: 0.35rem 0 0.65rem; text-transform: uppercase; }
        .map-empty { align-items: center; background: radial-gradient(circle at 55% 40%, rgba(25, 181, 165, 0.2), transparent 38%), linear-gradient(145deg, #10283a, #0a1626); border: 1px dashed rgba(125, 211, 199, 0.34); border-radius: 7px; color: var(--muted); display: flex; flex-direction: column; justify-content: center; min-height: 276px; padding: 1.5rem; text-align: center; }
        .map-empty strong { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; margin-bottom: 0.45rem; }
        .intelligence-panel { background: #142338; border: 1px solid rgba(125, 211, 199, 0.25); border-radius: 8px; min-height: 100%; padding: 1.1rem; }
        .panel-heading { color: var(--text); font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 600; margin: 0.45rem 0 0.85rem; }
        .panel-risk { color: var(--teal-soft); font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; }
        .panel-copy { color: var(--muted); font-size: 0.82rem; line-height: 1.55; }
        .panel-rule { border-top: 1px solid var(--line); margin: 0.9rem 0; }
        .factor-chip { background: #0d1a2a; border: 1px solid var(--line); border-radius: 5px; color: var(--muted); display: inline-block; font-size: 0.72rem; margin: 0.15rem 0.2rem 0.15rem 0; padding: 0.35rem 0.45rem; }
        .factor-chip strong { color: var(--teal-soft); }
        .data-footnote { color: var(--muted); font-size: 0.72rem; line-height: 1.45; margin-top: 0.65rem; }
        @media (max-width: 1000px) { .kpi-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
        @media (max-width: 600px) { .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); } .command-shell { padding: 1rem; } }
        @media (max-width: 760px) { .block-container { padding: 2rem 1rem 4rem; } .flow-arrow { padding: 0.35rem 0; transform: rotate(90deg); } .risk-level { font-size: 2.2rem; } .history-row { grid-template-columns: 1fr 1fr; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():
    st.sidebar.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-name">RIVORA AI</div>
            <div class="brand-subtitle">Community Environmental Risk<br> &amp; Resilience Intelligence Platform</div>
            <div class="status-line">● &nbsp; Prototype · AI-assisted decision support</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sync_selected_risk_domain():
    """Copy the widget value into application state from its callback."""
    st.session_state["selected_risk_domain"] = st.session_state["risk_domain_selector"]


def page_header(kicker, title, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_domain_card(domain_name, config):
    st.markdown(
        f'<div class="surface-tight"><div class="surface-label">{html.escape(config["status"])}</div><div class="surface-title">{html.escape(domain_name)}</div><div class="surface-copy">{html.escape(config["summary"])}</div><div class="map-note">Source status · {html.escape(config["source"])}</div></div>',
        unsafe_allow_html=True,
    )


def render_prototype_domain(domain_name):
    config = RISK_DOMAINS[domain_name]
    st.markdown('<div class="section-kicker">Structured prototype assessment</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.markdown(f'<div class="surface-label">{html.escape(config["status"])}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="surface-copy">{html.escape(config["summary"])} This module does not produce a scientifically validated risk score or official warning.</div>', unsafe_allow_html=True)
    values = {}
    options = list(SEVERITY_OPTIONS)
    scenario = st.selectbox(
        "Prototype scenario",
        ["Custom manual inputs", "Lower exposure context", "Elevated exposure context"],
        key=f"domain_scenario_{domain_name}",
    )
    for index, field in enumerate(config["fields"]):
        values[field] = st.selectbox(field, options, key=f"domain_{domain_name}_{index}")
    scenario_values = {
        field: ("Low" if scenario == "Lower exposure context" else "High")
        for field in config["fields"]
    }
    assessment_values = values if scenario == "Custom manual inputs" else scenario_values
    if scenario != "Custom manual inputs":
        st.caption(f"Preset applied to all domain factors: {scenario}. Results are prototype scenario exploration, not a forecast.")
    if st.button("Review Prototype Assessment", type="primary", key=f"review_{domain_name}"):
        assessment = assess_domain(domain_name, assessment_values)
        st.session_state["prototype_domain_result"] = assessment
        st.session_state["prototype_domain_values"] = assessment_values
        add_assessment_record(
            domain_name,
            st.session_state.get("prototype_domain_location") or "Manual input",
            assessment.level,
            assessment.score,
            list(assessment.factors),
            assessment_values,
            list(assessment.actions),
        )
    result = st.session_state.get("prototype_domain_result")
    if result and result.domain == domain_name:
        score = result.score if result.score is not None else "—"
        gauge_width = 0 if result.score is None else round((result.score / result.maximum_score) * 100)
        st.markdown('<div class="section-kicker">Prototype risk result</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="risk-panel {result.level.lower().replace(" ", "-")}"><div class="risk-label">{html.escape(domain_name)}</div><div class="risk-level">{result.level}</div><div class="score-label">Relative prototype score</div><div class="score-value">{score}</div><div class="gauge-track"><div class="gauge-fill" style="width:{gauge_width}%"></div></div><div class="gauge-scale"><span>0</span><span>Prototype scale · not probability</span><span>{result.maximum_score}</span></div></div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns([1, 1.4])
        with left:
            st.markdown('<div class="surface"><div class="surface-label">Key drivers</div>', unsafe_allow_html=True)
            for factor, factor_score in result.factors.items():
                width = round((factor_score / 2) * 100)
                st.markdown(f'<div class="factor-row"><span class="factor-name">{html.escape(factor)}</span><span class="factor-score">{factor_score}</span></div><div class="driver-bar"><div class="driver-fill" style="width:{width}%"></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown(f'<div class="surface"><div class="surface-label">Explainability</div><p class="surface-copy">{html.escape(result.explanation)}</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-kicker">Interpretation status</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-row"><div class="status-chip">Classification <strong>● Prototype review</strong></div><div class="status-chip">Data <strong>● Manual inputs</strong></div><div class="status-chip">Official warning <strong>● Not provided</strong></div></div>', unsafe_allow_html=True)
        st.info(result.uncertainty)
        st.markdown('<div class="section-kicker">Recommended actions</div>', unsafe_allow_html=True)
        st.markdown("<ul class='action-list'>" + "".join(f"<li>{html.escape(action)}</li>" for action in result.actions) + "</ul>", unsafe_allow_html=True)
        st.markdown('<div class="section-kicker">Downloadable summary</div>', unsafe_allow_html=True)
        report = "\n".join([
            "RIVORA AI",
            "Community Environmental Risk & Resilience Intelligence Platform",
            f"Domain: {domain_name}",
            f"Location: {st.session_state.get('prototype_domain_location') or 'Manual input'}",
            f"Assessment timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Risk level: {result.level}",
            f"Relative prototype score: {result.score}",
            "",
            "Inputs:",
            *[f"- {field}: {value}" for field, value in assessment_values.items()],
            "",
            "Explanation:",
            result.explanation,
            "",
            "Recommended actions:",
            *[f"- {action}" for action in result.actions],
            "",
            "Uncertainty:",
            result.uncertainty,
            "",
            "This prototype assessment does not replace official warnings, forecasts or instructions from authorized authorities.",
        ])
        st.download_button("Download Assessment Summary", report, file_name="rivora-domain-assessment.txt", mime="text/plain", key=f"download_{domain_name}")
        render_history()
    st.markdown('</div>', unsafe_allow_html=True)
    safety_notice()


def safety_notice():
    st.markdown(
        '<div class="safety-panel">RIVORA AI provides relative AI-assisted risk interpretation. It does not replace official warnings, forecasts or instructions from authorized disaster-management agencies.</div>',
        unsafe_allow_html=True,
    )


def preparedness_actions():
    st.markdown('<div class="section-kicker">Preparedness actions</div>', unsafe_allow_html=True)
    columns = st.columns(3)
    for column, (title, items) in zip(columns, ACTION_GROUPS):
        with column:
            st.markdown('<div class="surface-tight">', unsafe_allow_html=True)
            st.markdown(f'<div class="action-title">{title}</div>', unsafe_allow_html=True)
            st.markdown("<ul class='action-list'>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


ACTION_GROUPS = [
    ("Before flooding", ["Monitor official weather and disaster-management information.", "Protect important documents and essential items.", "Prepare basic emergency supplies and identify safer routes."]),
    ("During flooding", ["Avoid unnecessary travel through flooded roads.", "Do not enter fast-moving or unknown-depth water.", "Stay away from electrical hazards and follow official instructions."]),
    ("After flooding", ["Follow official guidance before returning to affected areas.", "Avoid potentially contaminated floodwater.", "Take care around damaged infrastructure and report hazards."]),
]


def input_dict(rainfall_intensity, rainfall_duration, terrain, drainage, previous_flooding, water_accumulation):
    return {
        "rainfall_intensity": rainfall_intensity,
        "rainfall_duration_hours": rainfall_duration,
        "terrain": terrain,
        "drainage": drainage,
        "previous_flooding": previous_flooding,
        "water_accumulation": water_accumulation,
    }


def result_from_inputs(values):
    return assess_risk(RiskInput(**values))


def render_status(result, observation):
    weather_status = "Available" if observation is not None else "Manual / unavailable"
    risk_status = "Complete" if result is not None and result.level != "INSUFFICIENT DATA" else "Partial"
    st.markdown('<div class="section-kicker">Data status</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="status-row"><div class="status-chip">Weather reference <strong>● {weather_status}</strong></div><div class="status-chip">Risk inputs <strong>● {risk_status}</strong></div><div class="status-chip">Assessment <strong>● Deterministic</strong></div><div class="status-chip">Knowledge guidance <strong>● Grounded</strong></div></div>',
        unsafe_allow_html=True,
    )


def render_weather_snapshot(observation):
    if observation is None:
        return
    st.markdown('<div class="section-kicker">Reference weather snapshot</div>', unsafe_allow_html=True)
    cards = []
    if observation.recent_total_mm is not None:
        cards.append(("Recent rainfall", f"{observation.recent_total_mm:g} mm"))
    precipitation = optional_weather_field(observation, "precipitation_mm")
    temperature = optional_weather_field(observation, "temperature_c")
    wind_speed = optional_weather_field(observation, "wind_speed_kmh")
    if precipitation is not None:
        cards.append(("Current precipitation", f"{precipitation:g} mm"))
    if temperature is not None:
        cards.append(("Temperature", f"{temperature:g} °C"))
    if wind_speed is not None:
        cards.append(("Wind", f"{wind_speed:g} km/h"))
    if cards:
        columns = st.columns(min(len(cards), 4))
        for column, (label, value) in zip(columns, cards):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="surface-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
    period = optional_weather_field(observation, "observation_time") or "Recent 24-hour reference window"
    observation_timezone = optional_weather_field(observation, "timezone")
    timezone = f" · {observation_timezone}" if observation_timezone else ""
    st.caption(f"Reference data from Open-Meteo · observation period: {period}{timezone}. This is not an official warning or forecast.")


def render_location_map(observation):
    if observation is None:
        return
    st.markdown('<div class="section-kicker">General area</div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 1])
    with left:
        st.map({"lat": [observation.latitude], "lon": [observation.longitude]}, zoom=9, use_container_width=True)
        st.markdown('<div class="map-note">Approximate city/general-area reference only. This map does not identify an exact flood boundary.</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="surface"><div class="surface-label">Selected area</div><div class="surface-title">{html.escape(observation.location_name)}</div><div class="surface-copy">{html.escape(observation.country)}<br>Coordinates are used only to retrieve general reference weather data.</div></div>', unsafe_allow_html=True)


def render_risk_drivers(result):
    st.markdown('<div class="section-kicker">Risk drivers</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    if not result.factors:
        st.markdown('<div class="surface-copy">Risk drivers will appear when all required assessment inputs are available.</div>', unsafe_allow_html=True)
    else:
        maximums = {"rainfall_intensity": 3, "rainfall_duration": 3, "drainage": 2, "terrain": 2, "previous_flooding": 2, "water_accumulation": 3}
        for factor, score_value in result.factors.items():
            label = factor.replace("_", " ").title()
            width = round((score_value / maximums.get(factor, 3)) * 100)
            st.markdown(f'<div class="factor-row"><span class="factor-name">{label}</span><span class="factor-score">{score_value}</span></div><div class="driver-bar"><div class="driver-fill" style="width:{width}%"></div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_result(result, values, observation):
    level_class = result.level.lower().replace(" ", "-")
    score = result.score if result.score is not None else "—"
    gauge_width = 0 if result.score is None else min(100, round((result.score / 15) * 100))
    location = observation.location_name if observation else "Manual location / not fetched"
    rainfall_status = "Loaded" if observation else "Manual fallback"
    st.markdown('<div class="section-kicker">03 · Risk result</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="risk-panel {level_class}"><div class="risk-label">Risk assessment</div><div class="risk-level">{result.level}</div><div class="score-label">Relative risk score</div><div class="score-value">{score}</div><div class="gauge-track"><div class="gauge-fill" style="width:{gauge_width}%"></div></div><div class="gauge-scale"><span>0</span><span>Relative scale · not probability</span><span>15</span></div><div class="risk-meta">Location · {html.escape(location)}<br>Rainfall reference · {rainfall_status}<br>Assessment · Deterministic engine</div></div>',
        unsafe_allow_html=True,
    )
    render_status(result, observation)
    render_weather_snapshot(observation)
    render_location_map(observation)
    st.markdown('<div class="section-kicker">04 · Explainability</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.4])
    with left:
        render_risk_drivers(result)
    with right:
        st.markdown('<div class="surface"><div class="surface-label">Deterministic assessment</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="surface-copy">{html.escape(result.explanation)}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">05 · Uncertainty &amp; safety</div>', unsafe_allow_html=True)
    st.info(result.uncertainty)
    safety_notice()
    preparedness_actions()


def assessment_report(result, values, observation, assessed_at):
    location = observation.location_name if observation else "Manual location / not fetched"
    lines = [
        "RIVORA AI",
        "Flood Risk Assessment",
        "",
        f"Location: {location}",
        f"Assessment timestamp: {assessed_at}",
        f"Risk level: {result.level}",
        f"Relative risk score: {result.score}",
        "",
        "Input conditions:",
    ]
    lines.extend(f"- {key}: {value}" for key, value in values.items())
    lines.extend(["", "Risk drivers:"])
    lines.extend(f"- {key}: {value}" for key, value in result.factors.items())
    lines.extend(["", "Explainability summary:", result.explanation, "", "Preparedness actions:"])
    for title, items in ACTION_GROUPS:
        lines.append(title)
        lines.extend(f"- {item}" for item in items)
    lines.extend(["", "Uncertainty and safety:", result.uncertainty, "", "Data source:"])
    lines.append("Open-Meteo recent/reference weather data" if observation else "Manual inputs; no weather reference loaded")
    lines.extend(["", "This assessment is a prototype, relative risk interpretation and does not replace official warnings, forecasts or instructions from authorized disaster-management agencies."])
    return "\n".join(lines)


def parse_assessment_time(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        try:
            return datetime.strptime(str(value), "%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            return None


def add_assessment_record(domain, location, level, score, drivers, inputs, actions):
    st.session_state.setdefault("assessment_history", []).append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "domain": domain,
            "location": location or "Manual input",
            "level": level,
            "score": score,
            "drivers": drivers,
            "inputs": inputs,
            "actions": actions,
        }
    )


def history_export(records, filters):
    lines = [
        "RIVORA AI",
        "Environmental Intelligence Session Summary",
        "",
        "Session-based RIVORA assessment history; not measured environmental history.",
        f"Filters: {filters}",
        f"Assessment count: {len(records)}",
        "",
    ]
    for item in records:
        lines.extend(
            [
                f"{item['time']} | {item.get('domain', 'Flood & Waterlogging')} | {item['location']} | {item['level']} | score={item['score']}",
                "  Drivers: " + ", ".join(item.get("drivers", [])),
            ]
        )
    lines.extend(
        [
            "",
            "Scores are domain-specific relative prototype scores and should not be compared as environmental measurements.",
            "This session summary does not replace official warnings, forecasts or instructions from authorized authorities.",
        ]
    )
    return "\n".join(lines)


def render_analytics():
    page_header(
        "Session intelligence",
        "Analytics & Insights",
        "Understand how recorded RIVORA assessments changed during this session.",
    )
    all_history = st.session_state.get("assessment_history", [])
    if not all_history:
        st.markdown('<div class="empty-state"><strong>No assessment history yet.</strong><br>Complete an assessment to begin building your RIVORA intelligence timeline.</div>', unsafe_allow_html=True)
        st.caption("History is session-based and does not represent measured environmental history.")
        return

    domains = sorted({item.get("domain", "Flood & Waterlogging") for item in all_history})
    locations = sorted({item.get("location", "Manual input") for item in all_history})
    levels = ["LOW", "MODERATE", "HIGH", "VERY HIGH", "INSUFFICIENT DATA"]
    risk_priority = ["VERY HIGH", "HIGH", "MODERATE", "LOW", "INSUFFICIENT DATA"]
    filter_columns = st.columns(4)
    with filter_columns[0]:
        domain_filter = st.selectbox("Domain", ["All domains"] + domains, key="analytics_domain_filter")
    with filter_columns[1]:
        location_filter = st.selectbox("Location", ["All locations"] + locations, key="analytics_location_filter")
    with filter_columns[2]:
        level_filter = st.selectbox("Risk level", ["All levels"] + levels, key="analytics_level_filter")
    with filter_columns[3]:
        period_filter = st.selectbox("Time period", ["All session history", "Last 24 hours", "Last 7 days", "Last 30 days"], key="analytics_period_filter")

    now = datetime.now()
    cutoff = {"Last 24 hours": now - timedelta(hours=24), "Last 7 days": now - timedelta(days=7), "Last 30 days": now - timedelta(days=30)}.get(period_filter)
    records = []
    for item in all_history:
        item_domain = item.get("domain", "Flood & Waterlogging")
        item_location = item.get("location", "Manual input")
        item_level = item.get("level", "INSUFFICIENT DATA")
        item_time = parse_assessment_time(item.get("time"))
        if domain_filter != "All domains" and item_domain != domain_filter:
            continue
        if location_filter != "All locations" and item_location != location_filter:
            continue
        if level_filter != "All levels" and item_level != level_filter:
            continue
        if cutoff and (item_time is None or item_time < cutoff):
            continue
        records.append(item)

    if not records:
        st.markdown('<div class="empty-state"><strong>No recorded assessments match these filters.</strong><br>Try a wider time period or complete another assessment.</div>', unsafe_allow_html=True)
        return

    latest = max(records, key=lambda item: parse_assessment_time(item.get("time")) or datetime.min)
    scores = [item["score"] for item in records if isinstance(item.get("score"), (int, float))]
    high_count = sum(item.get("level") in {"HIGH", "VERY HIGH"} for item in records)
    active_domain = st.session_state.get("selected_risk_domain", latest.get("domain", "Flood & Waterlogging"))
    selected_location = st.session_state.get("risk_location_query") or st.session_state.get("prototype_domain_location") or latest.get("location", "Manual input")
    kpis = [
        ("Total assessments", str(len(records))),
        ("Current selected level", str(st.session_state.get("risk_result").level if st.session_state.get("risk_result") else (st.session_state.get("prototype_domain_result").level if st.session_state.get("prototype_domain_result") else latest.get("level")))),
        ("Highest observed level", next((level for level in risk_priority if any(item.get("level") == level for item in records)), "INSUFFICIENT DATA")),
        ("High / very high", str(high_count)),
        ("Active domain", active_domain),
        ("Selected location", selected_location),
        ("Latest assessment", latest.get("time", "Unknown")),
    ]
    st.markdown('<div class="section-kicker">Recorded assessment status</div>', unsafe_allow_html=True)
    for start in range(0, len(kpis), 4):
        columns = st.columns(min(4, len(kpis) - start))
        for column, (label, value) in zip(columns, kpis[start:start + 4]):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="surface-label">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">RIVORA assessment history</div>', unsafe_allow_html=True)
    st.markdown('<div class="analytics-note">These records show changes in user-created RIVORA assessments, not changes in measured environmental conditions.</div>', unsafe_allow_html=True)
    trend_records = sorted(records, key=lambda item: parse_assessment_time(item.get("time")) or datetime.min)
    trend_values = [item.get("score") for item in trend_records if isinstance(item.get("score"), (int, float))]
    if len(trend_values) >= 2:
        st.line_chart({"Recorded relative score": trend_values}, use_container_width=True)
    elif len(trend_values) == 1:
        st.info("One numeric assessment is recorded. Complete another assessment to show a time-based change.")
    else:
        st.caption("No numeric scores are available for the selected records.")

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-kicker">Risk distribution</div>', unsafe_allow_html=True)
        distribution = Counter(item.get("level", "INSUFFICIENT DATA") for item in records)
        st.bar_chart(
            {"Risk level": levels, "Recorded assessments": [distribution.get(level, 0) for level in levels]},
            x="Risk level",
            y="Recorded assessments",
            use_container_width=True,
        )
    with right:
        st.markdown('<div class="section-kicker">Recorded assessments by domain</div>', unsafe_allow_html=True)
        domain_counts = Counter(item.get("domain", "Flood & Waterlogging") for item in records)
        recorded_domains = sorted(domain_counts)
        st.bar_chart(
            {"Domain": recorded_domains, "Recorded assessments": [domain_counts[domain] for domain in recorded_domains]},
            x="Domain",
            y="Recorded assessments",
            use_container_width=True,
        )
    st.caption("Domain scores and distributions are domain-specific relative prototype outputs; they are not directly comparable environmental measurements.")

    st.markdown('<div class="section-kicker">Recorded assessments by location</div>', unsafe_allow_html=True)
    location_counts = Counter(item.get("location", "Manual input") for item in records)
    recorded_locations = sorted(location_counts)
    st.bar_chart(
        {"Location": recorded_locations, "Recorded assessments": [location_counts[location] for location in recorded_locations]},
        x="Location",
        y="Recorded assessments",
        use_container_width=True,
    )
    st.caption("Recorded RIVORA assessments by location. A small session dataset should not be used to rank locations objectively.")
    render_history()

    st.markdown('<div class="section-kicker">Compare two recorded assessments</div>', unsafe_allow_html=True)
    if len(records) < 2:
        st.info("Complete at least two assessments to compare recorded results.")
    else:
        options = [f"{index + 1} · {item.get('time')} · {item.get('domain', 'Flood & Waterlogging')} · {item.get('location', 'Manual input')} · {item.get('level')}" for index, item in enumerate(records)]
        first_index = st.selectbox("Assessment A", range(len(records)), format_func=lambda index: options[index], key="analytics_compare_a")
        second_index = st.selectbox("Assessment B", range(len(records)), index=min(1, len(records) - 1), format_func=lambda index: options[index], key="analytics_compare_b")
        first, second = records[first_index], records[second_index]
        compare_columns = st.columns(2)
        for column, label, item in zip(compare_columns, ["Assessment A", "Assessment B"], [first, second]):
            with column:
                inputs = item.get("inputs", {})
                actions = item.get("actions", [])
                input_text = "; ".join(f"{key.replace('_', ' ')}: {value}" for key, value in inputs.items()) or "Not recorded"
                action_text = "; ".join(actions[:2]) or "Not recorded"
                st.markdown(f'<div class="surface"><div class="surface-label">{label}</div><div class="surface-title">{html.escape(item.get("domain", "Flood & Waterlogging"))}</div><div class="surface-copy">{html.escape(item.get("location", "Manual input"))}<br>{html.escape(item.get("time", "Unknown"))}</div><div class="risk-level">{item.get("level", "INSUFFICIENT DATA")}</div><div class="score-value">Score · {item.get("score", "—")}</div><div class="analytics-note">Drivers: {html.escape(", ".join(item.get("drivers", [])) or "Not recorded")}<br>Inputs: {html.escape(input_text)}<br>Actions: {html.escape(action_text)}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Export filtered history</div>', unsafe_allow_html=True)
    filter_summary = f"domain={domain_filter}; location={location_filter}; level={level_filter}; period={period_filter}"
    st.download_button("Download Analytics Summary", history_export(records, filter_summary), file_name="rivora-analytics-summary.txt", mime="text/plain", key="download_analytics")
    st.caption("Future versions can connect authoritative environmental time-series sources. This page currently uses session-based RIVORA assessment records only.")


def render_command_center():
    history = st.session_state.get("assessment_history", [])
    current_result = st.session_state.get("risk_result") or st.session_state.get("prototype_domain_result")
    selected_domain = st.session_state.get("selected_risk_domain", "Flood & Waterlogging")
    selected_location = st.session_state.get("risk_location_query") or st.session_state.get("prototype_domain_location") or "No location selected"
    latest = max(history, key=lambda item: parse_assessment_time(item.get("time")) or datetime.min) if history else None
    risk_level = current_result.level if current_result else (latest.get("level", "INSUFFICIENT DATA") if latest else "INSUFFICIENT DATA")
    risk_score = current_result.score if current_result and current_result.score is not None else (latest.get("score", "—") if latest else "—")
    factors = current_result.factors if current_result else {}
    dominant_factors = sorted(factors.items(), key=lambda item: item[1], reverse=True)[:3]
    confidence = "Reference + manual" if st.session_state.get("risk_rainfall_observation") else ("Manual inputs" if current_result else "Awaiting assessment")
    preparedness = "Review actions" if current_result else "Not assessed"

    st.markdown(
        f'<div class="command-shell"><div class="command-meta">RIVORA AI · ENVIRONMENTAL INTELLIGENCE COMMAND CENTER</div><div class="command-title">Situation overview</div><div class="command-subtitle">A focused view of environmental context, deterministic risk analysis and preparedness decisions for {html.escape(selected_location)}.</div><div class="status-row"><div class="status-chip">Domain <strong>● {html.escape(selected_domain)}</strong></div><div class="status-chip">Data mode <strong>● {html.escape(confidence)}</strong></div><div class="status-chip">System <strong>● Prototype operational</strong></div></div></div>',
        unsafe_allow_html=True,
    )
    kpis = [
        ("Overall risk", risk_level, "Recorded prototype result" if history else "No assessment recorded"),
        ("Risk score", str(risk_score), "Relative prototype scale"),
        ("Active risk factors", str(len([value for value in factors.values() if value > 0])), "Derived from current result"),
        ("Assessments", str(len(history)), "Session records"),
        ("Data confidence", confidence, "Provenance-aware status"),
        ("Preparedness status", preparedness, "Guidance remains advisory"),
    ]
    st.markdown('<div class="kpi-strip">' + "".join(f'<div class="kpi-card"><div class="surface-label">{html.escape(label)}</div><div class="kpi-value">{html.escape(value)}</div><div class="kpi-context">{html.escape(context)}</div></div>' for label, value, context in kpis) + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="workspace-label">Geospatial workspace · reference context</div>', unsafe_allow_html=True)
    map_column, summary_column = st.columns([1.65, 0.9], gap="medium")
    with map_column:
        control_columns = st.columns([1.1, 1.1, 1.1, 0.9, 0.9])
        with control_columns[0]:
            st.radio("Basemap", ["Street", "Terrain", "Satellite"], key="command_basemap", horizontal=True)
        with control_columns[1]:
            st.selectbox("Layer", ["Assessment locations", "Risk layer · prototype", "Rainfall reference"], key="command_layer")
        with control_columns[2]:
            st.slider("Opacity", 0, 100, 75, key="command_opacity")
        with control_columns[3]:
            st.button("+ Zoom", key="command_zoom_in")
        with control_columns[4]:
            st.button("− Zoom", key="command_zoom_out")
        observation = st.session_state.get("risk_rainfall_observation")
        map_records = [item for item in history if isinstance(item.get("latitude"), (int, float)) and isinstance(item.get("longitude"), (int, float))]
        if observation and isinstance(observation.latitude, (int, float)) and isinstance(observation.longitude, (int, float)):
            map_records = map_records or [{"latitude": observation.latitude, "longitude": observation.longitude}]
        if map_records:
            st.map({"lat": [item["latitude"] for item in map_records], "lon": [item["longitude"] for item in map_records]}, zoom=9, use_container_width=True)
            st.caption(f"{st.session_state.get('command_basemap', 'Street')} basemap · {st.session_state.get('command_layer', 'Assessment locations')} · opacity {st.session_state.get('command_opacity', 75)}%")
        else:
            st.markdown('<div class="map-empty"><strong>No mapped assessment yet</strong><span>Run a rainfall reference lookup for a general area to place a source-backed location on the map.</span><span class="data-footnote">Satellite imagery and flood layers are unavailable in this prototype. This view does not claim current flooding.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="status-row"><div class="status-chip">Legend <strong>● Low · ● Moderate · ● High · ● Very high</strong></div><div class="status-chip">Layer status <strong>● Derived / prototype</strong></div></div>', unsafe_allow_html=True)
    with summary_column:
        factor_markup = "".join(f'<span class="factor-chip">{html.escape(name.replace("_", " "))} <strong>{value}</strong></span>' for name, value in dominant_factors) or '<span class="panel-copy">No active drivers recorded.</span>'
        explanation = current_result.explanation if current_result else "Complete a risk assessment to generate an evidence-aware explanation."
        uncertainty = current_result.uncertainty if current_result else "Uncertainty is high until an assessment and source context are available."
        action = "Review the preparedness guidance attached to the latest assessment." if current_result else "Open Risk Assessment and provide the available conditions."
        st.markdown(f'<div class="intelligence-panel"><div class="surface-label">Decision support</div><div class="panel-heading">Intelligence Summary</div><div class="panel-risk">{html.escape(risk_level)}</div><div class="panel-copy">{html.escape(selected_location)} · score {html.escape(str(risk_score))}</div><div class="panel-rule"></div><div class="surface-label">Dominant risk factors</div><div>{factor_markup}</div><div class="panel-rule"></div><div class="surface-label">Risk explanation</div><div class="panel-copy">{html.escape(explanation)}</div><div class="panel-rule"></div><div class="surface-label">Trend / change</div><div class="panel-copy">{html.escape("No measured trend; session records only." if len(history) < 2 else "Change shown only between recorded prototype assessments.")}</div><div class="panel-rule"></div><div class="surface-label">Uncertainty</div><div class="panel-copy">{html.escape(uncertainty)}</div><div class="panel-rule"></div><div class="surface-label">Recommended action</div><div class="panel-copy">{html.escape(action)}</div></div>', unsafe_allow_html=True)

    if history:
        st.markdown('<div class="workspace-label">Recorded intelligence · session history</div>', unsafe_allow_html=True)
        lower_left, lower_middle, lower_right = st.columns([1, 1, 1], gap="medium")
        distribution = Counter(item.get("level", "INSUFFICIENT DATA") for item in history)
        with lower_left:
            st.markdown('<div class="surface-tight"><div class="surface-label">Risk distribution</div><div class="surface-title">Recorded levels</div>', unsafe_allow_html=True)
            st.bar_chart({"Risk level": ["LOW", "MODERATE", "HIGH", "VERY HIGH"], "Assessments": [distribution.get(level, 0) for level in ["LOW", "MODERATE", "HIGH", "VERY HIGH"]]}, x="Risk level", y="Assessments", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with lower_middle:
            trend_records = sorted(history, key=lambda item: parse_assessment_time(item.get("time")) or datetime.min)
            trend_values = [item.get("score") for item in trend_records if isinstance(item.get("score"), (int, float))]
            st.markdown('<div class="surface-tight"><div class="surface-label">Assessment timeline</div><div class="surface-title">Recorded relative score</div>', unsafe_allow_html=True)
            if trend_values:
                st.line_chart({"Risk score": trend_values}, use_container_width=True)
            else:
                st.caption("No numeric scores recorded yet.")
            st.markdown('</div>', unsafe_allow_html=True)
        with lower_right:
            recent = sorted(history, key=lambda item: parse_assessment_time(item.get("time")) or datetime.min, reverse=True)[:5]
            st.markdown('<div class="surface-tight"><div class="surface-label">Recent assessments</div><div class="surface-title">Latest records</div>', unsafe_allow_html=True)
            for item in recent:
                st.markdown(f'<div class="history-row"><strong>{html.escape(item.get("location", "Manual input"))}</strong><span>{html.escape(item.get("domain", "Unknown"))}</span><span>{html.escape(item.get("level", "INSUFFICIENT DATA"))}</span><span>{html.escape(str(item.get("score", "—")))}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><strong>No assessment history yet.</strong><br>Complete a risk assessment to populate distribution, timeline and recent-record intelligence.</div>', unsafe_allow_html=True)

    st.markdown('<div class="workspace-label">Domain intelligence status</div>', unsafe_allow_html=True)
    domain_columns = st.columns(3)
    for column, (domain_name, config) in zip(domain_columns, list(RISK_DOMAINS.items())[:3]):
        with column:
            st.markdown(f'<div class="surface-tight"><div class="surface-label">{html.escape(config["status"])}</div><div class="surface-title">{html.escape(domain_name)}</div><div class="surface-copy">{html.escape(config["source"])}</div></div>', unsafe_allow_html=True)
    st.caption("Observed/reference data, derived prototype analysis and AI interpretation are kept distinct. RIVORA AI is not an official warning system.")
    safety_notice()


def render_record_comparison(records):
    if len(records) < 2:
        st.markdown('<div class="empty-state"><strong>Two recorded assessments are needed.</strong><br>Complete another assessment to compare RIVORA results.</div>', unsafe_allow_html=True)
        return
    options = [f"{index + 1} · {item.get('time')} · {item.get('domain', 'Flood & Waterlogging')} · {item.get('location', 'Manual input')} · {item.get('level')}" for index, item in enumerate(records)]
    first_index = st.selectbox("Assessment A", range(len(records)), format_func=lambda index: options[index], key="compare_page_a")
    second_index = st.selectbox("Assessment B", range(len(records)), index=min(1, len(records) - 1), format_func=lambda index: options[index], key="compare_page_b")
    columns = st.columns(2)
    for column, label, item in zip(columns, ["Assessment A", "Assessment B"], [records[first_index], records[second_index]]):
        with column:
            inputs = item.get("inputs", {})
            actions = item.get("actions", [])
            input_text = "; ".join(f"{key.replace('_', ' ')}: {value}" for key, value in inputs.items()) or "Not recorded"
            st.markdown(f'<div class="surface"><div class="surface-label">{label}</div><div class="surface-title">{html.escape(item.get("domain", "Flood & Waterlogging"))}</div><div class="surface-copy">{html.escape(item.get("location", "Manual input"))}<br>{html.escape(item.get("time", "Unknown"))}</div><div class="risk-level">{item.get("level", "INSUFFICIENT DATA")}</div><div class="score-value">Score · {item.get("score", "—")}</div><div class="analytics-note">Drivers: {html.escape(", ".join(item.get("drivers", [])) or "Not recorded")}<br>Inputs: {html.escape(input_text)}<br>Uncertainty: recorded prototype result<br>Actions: {html.escape("; ".join(actions[:2]) or "Not recorded")}</div></div>', unsafe_allow_html=True)


def render_compare_page():
    page_header("Intelligence comparison", "Compare Assessments", "Compare saved session records without implying measured environmental change.")
    records = st.session_state.get("assessment_history", [])
    render_record_comparison(records)
    st.caption("A comparison describes changes between recorded RIVORA assessments. It does not establish that environmental conditions changed by the same amount.")


def render_history_page():
    page_header("Session records", "Assessment History", "Review and manage the assessments created in this browser session.")
    records = st.session_state.get("assessment_history", [])
    if not records:
        st.markdown('<div class="empty-state"><strong>No assessment history yet.</strong><br>Complete an assessment to begin building your RIVORA intelligence timeline.</div>', unsafe_allow_html=True)
        return
    render_history()
    st.download_button("Download Session History", history_export(records, "all session records"), file_name="rivora-session-history.txt", mime="text/plain", key="download_history_page")
    st.caption("Session history is local to the current prototype session. No cloud or persistent personal-data storage is used.")


def render_responsible_ai_page():
    page_header("Trust layer", "Responsible AI", "The boundaries that keep RIVORA AI useful, explainable and accountable.")
    principles = [
        ("Transparency", "Every result identifies its domain, inputs, data status and prototype or deterministic status."),
        ("Explainability", "Risk drivers and plain-language reasons are shown beside the result."),
        ("Uncertainty", "Missing information produces INSUFFICIENT DATA or an explicit prototype limitation."),
        ("Privacy", "The interface requests city or general-area context and keeps history in session state."),
        ("Fairness", "The platform avoids claims that a small session sample ranks communities or people."),
        ("Human oversight", "Users and authorized authorities remain responsible for real-world decisions."),
        ("Safety boundary", "RIVORA AI does not replace official warnings, forecasts, evacuation orders or instructions."),
        ("Hallucination prevention", "No fabricated measurements, government alerts, accuracy statistics or environmental history are presented."),
    ]
    for start in range(0, len(principles), 2):
        columns = st.columns(2)
        for column, (title, copy) in zip(columns, principles[start:start + 2]):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    safety_notice()


def render_future_architecture_page():
    page_header("Future scope", "Future Production Architecture", "A roadmap for authoritative environmental data without pretending those integrations exist today.")
    steps = [
        ("01", "Authoritative data", "Future IMD, CWC, NDMA/SACHET, weather, air-quality, river, GIS and satellite sources."),
        ("02", "RIVORA data layer", "Validated adapters, provenance, timestamps, quality checks and domain-specific freshness."),
        ("03", "Domain assessment engines", "Deterministic or scientifically validated domain models with explicit uncertainty."),
        ("04", "Evidence and explanation", "RAG-grounded guidance with source traceability; LLMs remain explanation components."),
        ("05", "Decision support", "Preparedness guidance, dashboards and future notification channels subject to human authority."),
    ]
    for number, title, copy in steps:
        st.markdown(f'<div class="surface-tight"><div class="surface-label">{number} · FUTURE</div><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.caption("This roadmap is architecture documentation only. No government feed, satellite processing, production cloud infrastructure or notification service is implemented in this prototype.")
    safety_notice()


def render_evidence_page():
    page_header("Evidence layer", "Evidence & Trust", "Knowledge, provenance and responsible-use boundaries for the RIVORA platform.")
    st.markdown('<div class="section-kicker">Evidence / knowledge areas</div>', unsafe_allow_html=True)
    categories = [
        ("01", "Flood & waterlogging fundamentals", "Curated concepts supporting the mature flood domain."),
        ("02", "Environmental risk domains", "Prototype assumptions for heat, air, water, agriculture, river and waste domains."),
        ("03", "Preparedness and safety", "Action-oriented guidance with official authorities remaining authoritative."),
        ("04", "RAG and source traceability", "Knowledge-grounded explanation paths where the existing architecture supports them."),
    ]
    for start in range(0, len(categories), 2):
        columns = st.columns(2)
        for column, (number, title, copy) in zip(columns, categories[start:start + 2]):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="evidence-index">{number}</div><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Provenance categories</div>', unsafe_allow_html=True)
    st.markdown('<div class="status-row"><div class="status-chip">Authoritative <strong>● Official authorities</strong></div><div class="status-chip">Supplemental <strong>● Reference knowledge</strong></div><div class="status-chip">User-provided <strong>● Manual inputs</strong></div><div class="status-chip">Prototype <strong>● Assumptions / domain review</strong></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">What RIVORA AI does not know</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface-copy">This prototype does not provide fabricated measurements, official warnings, persistent environmental history, validated cross-domain forecasts, or automatic local instructions.</div>', unsafe_allow_html=True)
    safety_notice()


def render_history():
    history = st.session_state.get("assessment_history", [])
    if not history:
        return
    st.markdown('<div class="section-kicker">Assessment history · current session</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.markdown('<div class="history-row"><strong>Time</strong><strong>Domain</strong><strong>Area</strong><strong>Risk · score</strong></div>', unsafe_allow_html=True)
    for item in reversed(history[-8:]):
        domain = item.get("domain", "Flood & Waterlogging")
        st.markdown(f'<div class="history-row"><span>{item["time"]}</span><span>{html.escape(domain)}</span><span>{html.escape(item["location"])}</span><strong>{item["level"]} · {item["score"]}</strong></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Clear session history", key="clear_history"):
        st.session_state["assessment_history"] = []
        st.rerun()


def render_scenario_explorer(values):
    st.markdown('<div class="section-kicker">Scenario explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-label">Scenario exploration — not a forecast</div><div class="surface-copy">Adjust the existing inputs to explore how the deterministic prototype responds. This does not predict future conditions.</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        scenario_intensity = st.selectbox("Scenario rainfall intensity", ["Light", "Moderate", "Heavy", "Very Heavy", "Unknown"], index=["Light", "Moderate", "Heavy", "Very Heavy", "Unknown"].index(values["rainfall_intensity"]), key="scenario_intensity")
        scenario_duration = st.number_input("Scenario rainfall duration (hours)", 0.0, 72.0, float(values["rainfall_duration_hours"]), 0.5, key="scenario_duration")
        scenario_terrain = st.selectbox("Scenario terrain / elevation", ["Elevated", "Normal", "Low-lying", "Unknown"], index=["Elevated", "Normal", "Low-lying", "Unknown"].index(values["terrain"]), key="scenario_terrain")
    with right:
        scenario_drainage = st.selectbox("Scenario drainage condition", ["Good", "Moderate", "Poor", "Unknown"], index=["Good", "Moderate", "Poor", "Unknown"].index(values["drainage"]), key="scenario_drainage")
        scenario_previous = st.selectbox("Scenario previous flooding", ["None", "Occasional", "Frequent", "Unknown"], index=["None", "Occasional", "Frequent", "Unknown"].index(values["previous_flooding"]), key="scenario_previous")
        scenario_water = st.selectbox("Scenario existing water accumulation", ["None", "Minor", "Moderate", "Significant", "Unknown"], index=["None", "Minor", "Moderate", "Significant", "Unknown"].index(values["water_accumulation"]), key="scenario_water")
    if st.button("Run Scenario Assessment", type="secondary"):
        scenario_values = input_dict(scenario_intensity, scenario_duration, scenario_terrain, scenario_drainage, scenario_previous, scenario_water)
        st.session_state["scenario_values"] = scenario_values
        st.session_state["scenario_result"] = result_from_inputs(scenario_values)
    scenario_result = st.session_state.get("scenario_result")
    if scenario_result is not None:
        current_result = st.session_state.get("risk_result")
        compare_left, compare_right = st.columns(2)
        with compare_left:
            st.markdown(f'<div class="surface-tight"><div class="surface-label">Current risk</div><div class="compare-value">{current_result.level if current_result else "Not assessed"}</div><div class="delta-note">Score · {current_result.score if current_result else "—"}</div></div>', unsafe_allow_html=True)
        with compare_right:
            st.markdown(f'<div class="surface-tight"><div class="surface-label">Scenario risk</div><div class="compare-value">{scenario_result.level}</div><div class="delta-note">Score · {scenario_result.score if scenario_result.score is not None else "—"}</div></div>', unsafe_allow_html=True)
        changed = [key for key in values if values[key] != st.session_state["scenario_values"][key]]
        st.caption("Changed factors: " + (", ".join(key.replace("_", " ") for key in changed) if changed else "None"))
    st.markdown("</div>", unsafe_allow_html=True)


def render_flood_assessment():
    st.markdown('<div class="section-kicker">01 · Location &amp; live rainfall</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Recent rainfall reference</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface-copy">Use a city or general area only. Open-Meteo data is a recent reference signal, not an official flood warning. Exact private addresses are not needed.</div>', unsafe_allow_html=True)
    location_query = st.text_input("City or general area", placeholder="For example: Guwahati", help="Do not enter an exact private address or other personal information.", key="risk_location_query")
    if st.button("Fetch Recent Rainfall", type="secondary"):
        try:
            rainfall = fetch_recent_rainfall(location_query)
            st.session_state["risk_rainfall_intensity"] = rainfall.intensity
            st.session_state["risk_rainfall_duration"] = rainfall.duration_hours
            st.session_state["risk_rainfall_observation"] = rainfall
            st.success("Recent rainfall reference data loaded")
            st.caption(f"{rainfall.location_name}{', ' + rainfall.country if rainfall.country else ''} · {rainfall.recent_total_mm:g} mm over the recent 24-hour window · {rainfall.wet_hours:g} wet hours")
        except (LocationNotFoundError, RainfallDataMissingError, OpenMeteoUnavailableError) as exc:
            st.session_state.pop("risk_rainfall_observation", None)
            st.warning(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">02 · Community &amp; environmental conditions</div>', unsafe_allow_html=True)
    observation = st.session_state.get("risk_rainfall_observation")
    if observation is not None:
        st.caption("Rainfall fields were populated from Open-Meteo and remain editable. All other conditions are manual inputs.")
    st.session_state.setdefault("risk_rainfall_intensity", "Unknown")
    st.session_state.setdefault("risk_rainfall_duration", 1.0)
    left, right = st.columns(2)
    with left:
        rainfall_intensity = st.selectbox("Rainfall intensity", ["Light", "Moderate", "Heavy", "Very Heavy", "Unknown"], key="risk_rainfall_intensity")
        rainfall_duration = st.number_input("Rainfall duration (hours)", min_value=0.0, max_value=72.0, step=0.5, key="risk_rainfall_duration")
        terrain = st.selectbox("Terrain / elevation", ["Elevated", "Normal", "Low-lying", "Unknown"])
    with right:
        drainage = st.selectbox("Drainage condition", ["Good", "Moderate", "Poor", "Unknown"])
        previous_flooding = st.selectbox("Previous flooding", ["None", "Occasional", "Frequent", "Unknown"])
        water_accumulation = st.selectbox("Existing water accumulation", ["None", "Minor", "Moderate", "Significant", "Unknown"])
    current_values = input_dict(rainfall_intensity, rainfall_duration, terrain, drainage, previous_flooding, water_accumulation)
    if st.button("Assess Flood Risk", type="primary"):
        st.session_state["risk_inputs"] = current_values
        st.session_state["risk_result"] = result_from_inputs(current_values)
        observation = st.session_state.get("risk_rainfall_observation")
        add_assessment_record("Flood & Waterlogging", observation.location_name if observation else "Manual input", st.session_state["risk_result"].level, st.session_state["risk_result"].score, list(st.session_state["risk_result"].factors), current_values, [item for _, items in ACTION_GROUPS for item in items])
    result = st.session_state.get("risk_result")
    if result is not None:
        values = st.session_state.get("risk_inputs", current_values)
        render_result(result, values, st.session_state.get("risk_rainfall_observation"))
        st.markdown('<div class="section-kicker">Downloadable summary</div>', unsafe_allow_html=True)
        st.download_button("Download Assessment Summary", assessment_report(result, values, st.session_state.get("risk_rainfall_observation"), datetime.now().strftime("%Y-%m-%d %H:%M")), file_name="rivora-assessment-summary.txt", mime="text/plain", key="download_assessment")
        render_history()


inject_styles()
render_brand()


# ---------- NAVIGATION ----------
page = st.sidebar.radio(
    "Navigate",
    [
        "Overview · Command Center",
        "Intelligence · Risk Assessment",
        "Intelligence · Scenario Explorer",
        "Intelligence · Compare Assessments",
        "Intelligence · Insights & Analytics",
        "Environment · Flood & Waterlogging",
        "Environment · Heat Risk",
        "Environment · Air Quality",
        "Environment · Water Security",
        "Environment · Agriculture",
        "Environment · River & Erosion",
        "Environment · Waste & Environment",
        "Support · AI Preparedness Assistant",
        "Support · Assessment History",
        "Support · Evidence & Trust",
        "Support · Responsible AI",
        "Support · Future Production Architecture",
    ],
    label_visibility="collapsed",
)


# ---------- MAIN ----------
if page == "Overview · Command Center":
    render_command_center()
elif page == "Intelligence · Risk Assessment" or page.startswith("Environment ·"):
    page_header("Environmental risk workspace", "Environmental Risk Assessment", "Select a community risk domain and interpret available conditions.")
    direct_domain = {
        "Environment · Flood & Waterlogging": "Flood & Waterlogging",
        "Environment · Heat Risk": "Heat Risk",
        "Environment · Air Quality": "Air Pollution",
        "Environment · Water Security": "Water Security",
        "Environment · Agriculture": "Agriculture & Environmental Stress",
        "Environment · River & Erosion": "River & Erosion",
        "Environment · Waste & Environment": "Waste & Environmental Concerns",
    }.get(page)
    if direct_domain:
        selected_domain = direct_domain
        st.session_state["selected_risk_domain"] = direct_domain
    else:
        selected_domain = st.session_state.get("selected_risk_domain", "Flood & Waterlogging")
        selected_domain = st.selectbox(
            "Risk domain",
            list(RISK_DOMAINS),
            index=list(RISK_DOMAINS).index(selected_domain),
            key="risk_domain_selector",
            on_change=sync_selected_risk_domain,
        )
    if direct_domain:
        st.markdown(f'<div class="status-row"><div class="status-chip">Active domain <strong>● {html.escape(selected_domain)}</strong></div><div class="status-chip">Status <strong>● {html.escape(RISK_DOMAINS[selected_domain]["status"])}</strong></div></div>', unsafe_allow_html=True)
    st.caption(RISK_DOMAINS[selected_domain]["summary"])
    if selected_domain != "Flood & Waterlogging":
        domain_location = st.text_input("City or general area", placeholder="For example: Guwahati", help="Use a city or general area only. Do not enter an exact private address.", key="prototype_domain_location")
        if domain_location:
            st.caption("Location context · " + domain_location + " · map/data integration planned for this domain")
        render_prototype_domain(selected_domain)
        st.stop()
    # Flood & Waterlogging continues below with its validated inputs and engine.
    render_flood_assessment()
    st.stop()

elif page == "Intelligence · Scenario Explorer":
    page_header("Prototype exploration", "Scenario Explorer", "Adjust the validated flood domain to explore relative assessment changes. This is not a forecast.")
    if st.session_state.get("risk_inputs"):
        render_scenario_explorer(st.session_state["risk_inputs"])
    else:
        st.markdown('<div class="empty-state"><strong>No baseline assessment yet.</strong><br>Complete a Flood &amp; Waterlogging assessment before exploring scenarios.</div>', unsafe_allow_html=True)

elif page == "Intelligence · Compare Assessments":
    render_compare_page()

elif page == "Intelligence · Insights & Analytics":
    render_analytics()

elif page == "Support · Assessment History":
    render_history_page()

elif page == "Support · Responsible AI":
    render_responsible_ai_page()

elif page == "Support · Future Production Architecture":
    render_future_architecture_page()

elif page == "Support · Evidence & Trust":
    render_evidence_page()
    st.stop()
    st.markdown(
        '<p class="hero-copy">An explainable AI platform for assessing community-level environmental risks, understanding contributing factors, and supporting practical preparedness and resilience decisions.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">A clear path from conditions to resilience</div>', unsafe_allow_html=True)
    flow = [
        ("01", "Environmental context", "Reference data and community inputs"),
        ("02", "Risk domains", "Flood, heat, air, water and land"),
        ("03", "Explainable assessment", "Drivers, uncertainty and trust"),
        ("04", "Resilience actions", "Practical guidance for communities"),
    ]
    columns = st.columns([1, 0.12, 1, 0.12, 1, 0.12, 1])
    for index, (number, title, copy) in enumerate(flow):
        with columns[index * 2]:
            st.markdown(
                f'<div class="surface"><div class="surface-label">{number}</div><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )
        if index < 3:
            with columns[index * 2 + 1]:
                st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Research alignment</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.8])
    with left:
        st.markdown(
            '<div class="surface"><div class="surface-label">Primary alignment</div><div class="sdg-number">SDG 11</div><div class="sdg-label">Sustainable Cities and Communities</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="surface"><div class="surface-label">Secondary alignment</div><div class="sdg-number">SDG 13 · SDG 6</div><div class="sdg-label">Climate Action · Clean Water and Sanitation</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Risk intelligence portfolio</div>', unsafe_allow_html=True)
    domain_columns = st.columns(2)
    for index, (domain_name, config) in enumerate(RISK_DOMAINS.items()):
        with domain_columns[index % 2]:
            render_domain_card(domain_name, config)
        if index % 2 == 1:
            st.markdown("<br>", unsafe_allow_html=True)
    safety_notice()


# ---------- LEGACY FLOOD BODY ----------
elif page == "__legacy_flood_body__":
    page_header(
        "Environmental risk workspace",
        "Environmental Risk Assessment",
        "Select a community risk domain and interpret available conditions.",
    )

    selected_domain = st.session_state.get("selected_risk_domain", "Flood & Waterlogging")
    selected_domain = st.selectbox(
        "Risk domain",
        list(RISK_DOMAINS),
        index=list(RISK_DOMAINS).index(selected_domain),
        key="risk_domain_selector",
        on_change=sync_selected_risk_domain,
    )
    st.caption(RISK_DOMAINS[selected_domain]["summary"])
    if selected_domain != "Flood & Waterlogging":
        domain_location = st.text_input(
            "City or general area",
            placeholder="For example: Guwahati",
            help="Use a city or general area only. Do not enter an exact private address.",
            key="prototype_domain_location",
        )
        if domain_location:
            st.caption("Location context · " + domain_location + " · map/data integration planned for this domain")
        render_prototype_domain(selected_domain)
        st.stop()

    st.markdown('<div class="section-kicker">01 · Location &amp; live rainfall</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface"><div class="surface-title">Recent rainfall reference</div>', unsafe_allow_html=True)
    st.markdown('<div class="surface-copy">Use a city or general area only. Open-Meteo data is a recent reference signal, not an official flood warning. Exact private addresses are not needed.</div>', unsafe_allow_html=True)
    location_query = st.text_input(
        "City or general area",
        placeholder="For example: Guwahati",
        help="Do not enter an exact private address or other personal information.",
        key="risk_location_query",
    )
    if st.button("Fetch Recent Rainfall", type="secondary"):
        try:
            rainfall = fetch_recent_rainfall(location_query)
            st.session_state["risk_rainfall_intensity"] = rainfall.intensity
            st.session_state["risk_rainfall_duration"] = rainfall.duration_hours
            st.session_state["risk_rainfall_observation"] = rainfall
            st.success("Recent rainfall reference data loaded")
            st.caption(f"{rainfall.location_name}{', ' + rainfall.country if rainfall.country else ''} · {rainfall.recent_total_mm:g} mm over the recent 24-hour window · {rainfall.wet_hours:g} wet hours")
        except (LocationNotFoundError, RainfallDataMissingError, OpenMeteoUnavailableError) as exc:
            st.session_state.pop("risk_rainfall_observation", None)
            st.warning(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">02 · Community &amp; environmental conditions</div>', unsafe_allow_html=True)
    observation = st.session_state.get("risk_rainfall_observation")
    if observation is not None:
        st.caption("Rainfall fields were populated from Open-Meteo and remain editable. All other conditions are manual inputs.")
    st.session_state.setdefault("risk_rainfall_intensity", "Unknown")
    st.session_state.setdefault("risk_rainfall_duration", 1.0)
    left, right = st.columns(2)
    with left:
        rainfall_intensity = st.selectbox("Rainfall intensity", ["Light", "Moderate", "Heavy", "Very Heavy", "Unknown"], key="risk_rainfall_intensity")
        rainfall_duration = st.number_input("Rainfall duration (hours)", min_value=0.0, max_value=72.0, step=0.5, key="risk_rainfall_duration")
        terrain = st.selectbox("Terrain / elevation", ["Elevated", "Normal", "Low-lying", "Unknown"])
    with right:
        drainage = st.selectbox("Drainage condition", ["Good", "Moderate", "Poor", "Unknown"])
        previous_flooding = st.selectbox("Previous flooding", ["None", "Occasional", "Frequent", "Unknown"])
        water_accumulation = st.selectbox("Existing water accumulation", ["None", "Minor", "Moderate", "Significant", "Unknown"])

    st.markdown("<br>", unsafe_allow_html=True)
    current_values = input_dict(
        rainfall_intensity,
        rainfall_duration,
        terrain,
        drainage,
        previous_flooding,
        water_accumulation,
    )
    if st.button("Assess Flood Risk", type="primary"):
        st.session_state["risk_inputs"] = current_values
        st.session_state["risk_result"] = result_from_inputs(current_values)
        observation = st.session_state.get("risk_rainfall_observation")
        add_assessment_record(
            "Flood & Waterlogging",
            observation.location_name if observation else "Manual input",
            st.session_state["risk_result"].level,
            st.session_state["risk_result"].score,
            list(st.session_state["risk_result"].factors),
            current_values,
            [item for _, items in ACTION_GROUPS for item in items],
        )
    result = st.session_state.get("risk_result")
    if result is not None:
        values = st.session_state.get("risk_inputs", current_values)
        observation = st.session_state.get("risk_rainfall_observation")
        render_result(result, values, observation)
        render_scenario_explorer(values)
        st.markdown('<div class="section-kicker">Downloadable summary</div>', unsafe_allow_html=True)
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.download_button(
            "Download Assessment Summary",
            assessment_report(result, values, observation, report_time),
            file_name="rivora-assessment-summary.txt",
            mime="text/plain",
            key="download_assessment",
        )
        render_history()


# ---------- ANALYTICS ----------
elif page == "Analytics":
    render_analytics()


# ---------- PREPAREDNESS ----------
elif page == "Support · AI Preparedness Assistant":
    page_header(
        "Grounded knowledge assistant",
        "Preparedness Assistant",
        "Ask about practical flood preparedness and safety.",
    )
    st.markdown('<div class="surface"><div class="surface-label">Guided questions</div>', unsafe_allow_html=True)
    st.markdown('<div class="prompt-note">Choose a practical situation. Responses stay within the prototype safety guidance and do not provide location-specific evacuation instructions.</div>', unsafe_allow_html=True)
    prompt_groups = [
        ("Before flooding", "What should I prepare before heavy rainfall?"),
        ("During flooding", "What should I do during road flooding?"),
        ("After flooding", "What should I do after flooding?"),
    ]
    prompt_columns = st.columns(3)
    for column, (group, prompt) in zip(prompt_columns, prompt_groups):
        with column:
            st.markdown(f'<div class="surface-label">{group}</div>', unsafe_allow_html=True)
            if st.button(prompt, key=f"prompt_{prompt}"):
                st.session_state["assistant_question"] = prompt
    question = st.text_input(
        "Your question",
        placeholder="Ask about practical flood preparedness",
        key="assistant_question",
    )
    if question:
        query = question.lower()
        st.markdown('<div class="section-kicker">Response</div>', unsafe_allow_html=True)
        if "during" in query or "road" in query or "travel" in query:
            st.warning("Avoid unnecessary travel through flooded roads. Never enter fast-moving or unknown-depth water and follow official instructions.")
        elif "before" in query or "prepare" in query:
            st.info("Monitor official information, protect important documents, prepare essential supplies and identify safer routes.")
        elif "after" in query:
            st.info("Follow official guidance before returning. Avoid contaminated water and be cautious around damaged infrastructure and electricity.")
        else:
            st.info("For safety-critical situations, follow instructions from authorized disaster-management and government agencies.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    safety_notice()


# ---------- EVIDENCE ----------
else:
    page_header(
        "Evidence layer",
        "Evidence & Knowledge Base",
        "A curated foundation for transparent flood-risk interpretation and preparedness guidance.",
    )
    st.markdown('<div class="section-kicker">Evidence / knowledge</div>', unsafe_allow_html=True)
    categories = [
        ("01", "Flood & waterlogging fundamentals", "Core concepts for understanding flood and waterlogging conditions."),
        ("02", "Rainfall & drainage factors", "Context for how rainfall intensity, duration and drainage shape relative risk."),
        ("03", "Community preparedness", "Practical guidance for preparing households and communities."),
        ("04", "Rural & agricultural impacts", "Considerations for rural settings and agricultural areas."),
        ("05", "River-related hazards", "Knowledge about river hazards, flow and erosion."),
        ("06", "Emergency preparedness", "Safety-oriented actions before, during and after flooding."),
        ("07", "Responsible AI & uncertainty", "Limitations, uncertainty and the boundaries of this prototype."),
    ]
    for start in range(0, len(categories), 2):
        columns = st.columns(2)
        for column, (number, title, copy) in zip(columns, categories[start:start + 2]):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="evidence-index">{number}</div><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Responsible AI safeguards</div>', unsafe_allow_html=True)
    safeguards = [
        ("Evidence supports the system", "Curated flood, rainfall, drainage, preparedness and hazard knowledge provides context for explanations and guidance."),
        ("Uncertainty stays visible", "Missing or incomplete inputs produce an explicit insufficient-data state rather than an invented conclusion."),
        ("Risk classification is deterministic", "The existing risk engine owns the level and score. An LLM cannot override or reclassify it."),
        ("Authorities remain authoritative", "Official disaster-management agencies remain the source for warnings, forecasts and emergency instructions."),
        ("Privacy by design", "The prototype asks for a city or general area, does not need exact private addresses, and keeps history in session state."),
        ("No fabricated signals", "The interface does not invent measurements, government alerts, accuracy statistics or operational forecasts."),
    ]
    for start in range(0, len(safeguards), 2):
        columns = st.columns(2)
        for column, (title, copy) in zip(columns, safeguards[start:start + 2]):
            with column:
                st.markdown(f'<div class="surface-tight"><div class="surface-title">{title}</div><div class="surface-copy">{copy}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    safety_notice()
    st.caption("Links and knowledge materials are for reference. RIVORA AI does not endorse third parties and does not replace official warnings.")
    