"""Display structured AI research results."""

from __future__ import annotations

import streamlit as st

from ai.research import ResearchResult
from utils.research_view import render_research_chart


def render_research_result(result: ResearchResult) -> None:
    """Render a structured AI research response."""
    st.markdown("### Research result")
    st.caption("Educational research only — not personalized financial advice.")

    header_left, header_right = st.columns([3, 1])
    with header_left:
        title = result.primary_ticker or "General research"
        st.markdown(f"**{title}**")
        if result.summary:
            st.write(result.summary)
    with header_right:
        st.metric("Recommendation", result.recommendation)
        st.metric("Confidence", f"{result.confidence_score}/100")

    st.progress(result.confidence_score / 100)

    st.markdown("#### Why this fits your profile")
    st.write(result.profile_fit or "No profile-fit explanation was provided.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Technical reasoning")
        st.write(result.technical_reasoning or "No technical reasoning was provided.")
    with col2:
        st.markdown("#### Fundamental reasoning")
        st.write(result.fundamental_reasoning or "No fundamental reasoning was provided.")

    st.markdown("#### News impact")
    st.write(result.news_impact or "No news impact analysis was provided.")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Risks")
        if result.risks:
            for risk in result.risks:
                st.markdown(f"- {risk}")
        else:
            st.write("No risks were identified.")
    with col4:
        st.markdown("#### Important uncertainties")
        if result.important_uncertainties:
            for item in result.important_uncertainties:
                st.markdown(f"- {item}")
        else:
            st.write("No major uncertainties were listed.")

    st.markdown("#### Investment horizon")
    st.write(result.investment_horizon or "No investment horizon was provided.")

    render_research_chart(result.primary_ticker)
