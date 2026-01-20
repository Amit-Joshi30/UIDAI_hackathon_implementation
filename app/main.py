"""
UIDAI Insight Command Center - Main Application
================================================
Experience-first architecture for judge memory.
90-second flow: Framing -> Proof -> Case File -> Decision -> Trust
"""

import sys
from pathlib import Path
import streamlit as st

# =============================================================================
# PATH FIX (Streamlit Cloud safe imports)
# =============================================================================
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="UIDAI Insight Command Center",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# HARD LOCK SIDEBAR (DISABLE COLLAPSE)
# =============================================================================
st.markdown(
    """
    <style>
    button[kind="header"] { display: none !important; }
    section[data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 280px !important;
        transform: none !important;
        visibility: visible !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("")

# =============================================================================
# IMPORTS
# =============================================================================
from config import STATIC_DIR
from data_handler import (
    preload_all_data,
    get_overview_metrics,
    get_state_summary,
    lookup_pincode,
    load_policy_recommendations,
)
from experiences.framing import render_framing, render_framing_minimal
from experiences.proof import render_proof
from experiences.case_file import render_case_file, render_case_file_header
from experiences.decision import render_decision
from experiences.trust import render_trust, render_trust_footer
from experiences.insights import render_insights

# =============================================================================
# LOAD CSS
# =============================================================================
def load_css():
    css_file = STATIC_DIR / "style.css"
    if css_file.exists():
        st.markdown(
            f"<style>{css_file.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

load_css()

# =============================================================================
# SESSION STATE
# =============================================================================
def init_session_state():
    defaults = {
        "data_loaded": False,
        "search_query": "",
        "selected_pincode": None,
        "selected_record": None,
        "current_view": "overview",
        "url_initialized": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_session_state()

# =============================================================================
# DATA LOADING
# =============================================================================
if not st.session_state.data_loaded:
    preload_all_data()
    st.session_state.data_loaded = True
    st.rerun()

# =============================================================================
# URL PARAMS — READ ONCE ONLY
# =============================================================================
if not st.session_state.url_initialized:
    params = st.query_params

    view = params.get("view")
    pincode = params.get("pincode")

    if view in {"overview", "analysis", "action", "insights"}:
        st.session_state.current_view = view

    if pincode and pincode.isdigit() and len(pincode) == 6:
        record = lookup_pincode(pincode)
        if record:
            st.session_state.search_query = pincode
            st.session_state.selected_pincode = pincode
            st.session_state.selected_record = record
            st.session_state.current_view = "analysis"

    st.session_state.url_initialized = True
    st.query_params.clear()

# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <h1 style="background:linear-gradient(135deg,#1A73E8,#FF9933);
                       -webkit-background-clip:text;
                       -webkit-text-fill-color:transparent;
                       font-size:1.4rem;font-weight:700;">
                UIDAI Insight Center
            </h1>
            <p style="color:#8B949E;font-size:0.8rem;">Decision Support System</p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        for key, label in {
            "overview": "Overview",
            "analysis": "Analysis",
            "action": "Action Plan",
            "insights": "Insights",
        }.items():
            if st.button(
                label,
                use_container_width=True,
                type="primary" if st.session_state.current_view == key else "secondary",
            ):
                st.session_state.current_view = key
                st.query_params["view"] = key
                if st.session_state.selected_pincode:
                    st.query_params["pincode"] = st.session_state.selected_pincode
                else:
                    st.query_params.pop("pincode", None)

        st.markdown("---")

        # ✅ PINCODE INPUT (EXACT ORIGINAL WORKING PATTERN)
        search = st.text_input(
            "Pincode",
            value=st.session_state.search_query,
            placeholder="Enter 6-digit pincode",
            key="search_input",
            label_visibility="collapsed",
        )

        # EXACT logic from original - NO view change, NO rerun
        if search != st.session_state.search_query:
            st.session_state.search_query = search
            if search.isdigit() and len(search) == 6:
                record = lookup_pincode(search)
                if record:
                    st.session_state.selected_pincode = search
                    st.session_state.selected_record = record
                    st.query_params["pincode"] = search

        if st.session_state.selected_record:
            if st.button("Clear", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.selected_pincode = None
                st.session_state.selected_record = None
                if "pincode" in st.query_params:
                    del st.query_params["pincode"]
                st.rerun()

        st.markdown(
            """
            <div style="margin-top:1rem;padding-top:0.5rem;
                        border-top:1px solid rgba(255,255,255,0.1);
                        text-align:center;">
                <span style="color:#8B949E;font-size:0.7rem;">
                    Team ID: <strong>UIDAI_2394</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

render_sidebar()

# =============================================================================
# MAIN CONTENT
# =============================================================================
def render_main():
    metrics = get_overview_metrics()
    state_summary = get_state_summary()
    policy_df = load_policy_recommendations(top_n=100)

    view = st.session_state.current_view

    if view == "overview":
        render_framing(total_pincodes=metrics.get("total_pincodes", 0))
        st.markdown("---")
        render_proof(
            state_summary=state_summary,
            metrics=metrics,
            district_count=metrics.get("total_districts", 0),
        )
        render_trust_footer()

    elif view == "analysis":
        render_framing_minimal()
        render_case_file_header()

        policy_record = None
        if st.session_state.selected_pincode and not policy_df.empty:
            match = policy_df[
                policy_df["pincode"] == st.session_state.selected_pincode
            ]
            if not match.empty:
                policy_record = match.iloc[0].to_dict()

        render_case_file(
            record=st.session_state.selected_record,
            policy_record=policy_record,
        )
        render_trust_footer()

    elif view == "action":
        render_framing_minimal()
        render_decision(metrics=metrics, policy_df=policy_df)
        render_trust_footer()

    elif view == "insights":
        render_insights()
        render_trust_footer()

render_main()
