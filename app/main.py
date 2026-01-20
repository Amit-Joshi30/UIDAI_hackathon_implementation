"""
UIDAI Insight Command Center - Main Application
================================================
Experience-first architecture for judge memory.
90-second flow: Framing -> Proof -> Case File -> Decision -> Trust
"""

import streamlit as st
from pathlib import Path

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="UIDAI Insight Command Center",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "UIDAI Insight Command Center - Hackathon 2026",
    },
)

# =============================================================================
# IMPORTS
# =============================================================================
from config import (
    AADHAAR_BLUE,
    SAFFRON,
    STATIC_DIR,
    COLOR_CRITICAL,
    COLOR_SUCCESS,
    TEXT_SECONDARY,
)

from data_handler import (
    preload_all_data,
    get_overview_metrics,
    get_state_summary,
    lookup_pincode,
    load_policy_recommendations,
    validate_data_sources,
)

# ✅ FIXED: all experience imports explicitly included
from .experiences.framing import render_framing, render_framing_minimal
from .experiences.proof import render_proof
from .experiences.case_file import render_case_file, render_case_file_header
from .experiences.decision import render_decision
from .experiences.trust import render_trust, render_trust_footer
from .experiences.insights import render_insights

# =============================================================================
# LOAD CSS
# =============================================================================
def load_css():
    css_file = STATIC_DIR / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
        if k not in st.session_state:
            st.session_state[k] = v


init_session_state()

# =============================================================================
# LOADING
# =============================================================================
def show_loading():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            """
            <div style="display:flex;flex-direction:column;align-items:center;
                        justify-content:center;min-height:60vh;text-align:center;">
                <h1 style="background:linear-gradient(135deg,#1A73E8,#FF9933);
                           -webkit-background-clip:text;
                           -webkit-text-fill-color:transparent;
                           font-size:2rem;font-weight:700;margin-bottom:1rem;">
                    UIDAI Insight Command Center
                </h1>
                <p style="color:#8B949E;font-size:0.9rem;">Initializing...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return placeholder


if not st.session_state.data_loaded:
    loading = show_loading()
    preload_all_data()
    st.session_state.data_loaded = True
    loading.empty()
    st.rerun()

# =============================================================================
# URL PARAMS (SAFE, ONE-TIME HYDRATION)
# =============================================================================
def handle_url_params():
    if st.session_state.url_initialized:
        return

    params = st.query_params

    if "view" in params and params["view"] in {
        "overview",
        "analysis",
        "action",
        "insights",
    }:
        st.session_state.current_view = params["view"]

    if "pincode" in params:
        pincode = params["pincode"]
        if pincode.isdigit() and len(pincode) == 6:
            record = lookup_pincode(pincode)
            if record:
                st.session_state.selected_pincode = pincode
                st.session_state.search_query = pincode
                st.session_state.selected_record = record

    st.session_state.url_initialized = True


handle_url_params()

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
                       font-size:1.4rem;font-weight:700;margin:0;">
                UIDAI Insight Center
            </h1>
            <p style="color:#8B949E;font-size:0.8rem;margin-top:0.25rem;">
                Decision Support System
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        views = {
            "overview": "Overview",
            "analysis": "Analysis",
            "action": "Action Plan",
            "insights": "Insights",
        }

        for key, label in views.items():
            selected = st.session_state.current_view == key
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.current_view = key
                st.experimental_set_query_params(
                    view=key,
                    pincode=st.session_state.selected_pincode
                    if st.session_state.selected_pincode
                    else None,
                )
                st.rerun()

        st.markdown("---")

        search = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="Enter 6-digit pincode",
            label_visibility="collapsed",
        )

        if search != st.session_state.search_query:
            st.session_state.search_query = search
            if search.isdigit() and len(search) == 6:
                record = lookup_pincode(search)
                if record:
                    st.session_state.selected_pincode = search
                    st.session_state.selected_record = record
                    st.experimental_set_query_params(
                        view=st.session_state.current_view, pincode=search
                    )

        if st.session_state.selected_record:
            if st.button("Clear", use_container_width=True):
                st.session_state.selected_pincode = None
                st.session_state.selected_record = None
                st.session_state.search_query = ""
                st.experimental_set_query_params(
                    view=st.session_state.current_view
                )
                st.rerun()

        st.markdown("---")

        status = validate_data_sources()
        healthy = all(status.values())
        color = "#3FB950" if healthy else "#F85149"
        text = "Systems operational" if healthy else "Data incomplete"

        st.markdown(
            f"""
            <div style="text-align:center;padding:0.5rem 0;">
                <span style="display:inline-block;width:6px;height:6px;
                             background:{color};border-radius:50%;
                             margin-right:6px;"></span>
                <span style="color:#6E7681;font-size:0.7rem;">{text}</span>
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
    data_status = validate_data_sources()

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
        if (
            st.session_state.selected_pincode
            and not policy_df.empty
        ):
            match = policy_df[
                policy_df["pincode"]
                == st.session_state.selected_pincode
            ]
            if not match.empty:
                policy_record = match.iloc[0].to_dict()

        render_case_file(
            record=st.session_state.selected_record,
            policy_record=policy_record,
        )

        render_trust(data_status)
        render_trust_footer()

    elif view == "action":
        render_framing_minimal()
        render_decision(metrics=metrics, policy_df=policy_df)
        render_trust(data_status)
        render_trust_footer()

    elif view == "insights":
        render_insights()
        render_trust_footer()


render_main()
