from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

COMPACT_CSS = """
.shell{height:100dvh!important;min-height:0!important;padding:6px!important;gap:6px!important;display:flex!important;flex-direction:column!important}
.sidebar{padding:8px!important;gap:6px!important;flex:0 0 auto}
.sidebar>div:first-child,.sidebar>.small{display:none!important}
.sidebar>.orb{display:grid!important;zoom:.65;height:150px!important;margin:0 auto}
.sidebar>.status{justify-content:center}
.sidebar .actions{display:flex!important;flex-direction:row!important;gap:6px!important;overflow-x:auto}
.sidebar .action{padding:7px 10px;font-size:12px;white-space:nowrap;flex:0 0 auto}
.sidebar>div[style*="margin-top:auto"]{display:flex;gap:6px;margin-top:0!important}
.sidebar>div[style*="margin-top:auto"] .action{width:auto!important;flex:1;margin-top:0!important}
.main{flex:1 1 auto!important;min-height:0!important}
header{padding:8px 12px!important}
h1{font-size:13px!important}
.feed{min-height:0!important;max-height:none!important;padding:12px!important}
.composer{padding:8px!important}
textarea{height:52px!important}
.notice{padding:0 10px 8px!important}
dialog{max-height:94dvh;overflow:auto}
"""

ORION_HTML = Path(__file__).with_name("AI_Agent.html")

def orion_widget():
    if "orion_open" not in st.session_state:
        st.session_state.orion_open = False

    st.markdown(
        """
        <style>
        .st-key-orion_fab   { position: fixed; bottom: 1.2rem; right: 1.2rem;
                              z-index: 99999; width: auto; }
        .st-key-orion_panel { position: fixed; bottom: 5rem; right: 1.2rem;
                              z-index: 99998; width: min(94vw, 460px); }
        .st-key-orion_fab button { padding: 0.7rem 1.3rem; font-size: 1.05rem; border-radius: 999px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # floating button (always visible)
    with st.container(key="orion_fab"):
        label = "✖ Close Orion" if st.session_state.orion_open else "🤖 Agent Orion"
        if st.button(label, key="orion_btn"):
            st.session_state.orion_open = not st.session_state.orion_open
            st.rerun()

    # the HTML is only loaded while the button has been clicked open
    if st.session_state.orion_open:
        with st.container(key="orion_panel"):
            html_code = ORION_HTML.read_text(encoding="utf-8").replace("</style>", COMPACT_CSS + "</style>", 1)
            components.html(html_code, height=620, scrolling=True)