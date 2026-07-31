CUSTOM_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&display=swap');
:root {
    --bg: #faf7f1;
    --bg-raised: #ffffff;
    --ink: #211d18;
    --ink-soft: #635c51;
    --ink-faint: #a49a8b;
    --line: #e6ddd0;
    --line-soft: #f0e9dd;
    --accent: #b4501f;
    --accent-soft: #f7e6da;
    --sage: #3f6b52;
    --sage-soft: #e7efe9;
    --amber: #b48a1f;
    --serif: "Source Serif 4", Georgia, serif;
    --sans: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
}
/* Hide default Streamlit chrome */
[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="collapsedControl"] { display: none; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stAppViewContainer"], .main {
    background: var(--bg) !important;
    color: var(--ink);
    font-family: var(--sans);
}
.block-container { max-width: 780px; padding-top: 1.2rem; }
h1, h2, h3 { font-family: var(--serif) !important; color: var(--ink) !important; }
/* Top nav */
.quire-topbar {
    display: flex; align-items: baseline; justify-content: space-between;
    padding: 6px 0 18px 0; border-bottom: 1px solid var(--line); margin-bottom: 22px;
}
.quire-wordmark { font-family: var(--serif); font-weight: 700; font-size: 1.5rem; color: var(--ink); letter-spacing: -0.01em; }
.quire-wordmark span { color: var(--accent); }
.quire-tagline { font-size: 0.78rem; color: var(--ink-faint); font-weight: 500; margin-top: 2px; }
.nav-pill button {
    background: transparent !important; color: var(--ink-soft) !important;
    border: none !important; border-radius: 20px !important;
    font-family: var(--sans) !important; font-weight: 600 !important; font-size: 0.82rem !important;
    padding: 6px 14px !important; box-shadow: none !important;
}
.nav-pill button:hover { color: var(--ink) !important; background: var(--line-soft) !important; }
.nav-pill-active button {
    background: var(--accent-soft) !important; color: var(--accent) !important;
}
/* Page heading block */
.page-kicker { font-size: 0.70rem; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase; color: var(--sage); margin-bottom: 4px; }
.page-heading { font-family: var(--serif); font-size: 1.9rem; font-weight: 700; color: var(--ink); letter-spacing: -0.01em; line-height: 1.15; }
.page-sub { font-size: 0.90rem; color: var(--ink-soft); margin-top: 6px; }
/* Empty-state hero (Ask page) */
.ask-hero { text-align: center; padding: 46px 0 30px 0; }
.ask-hero-title { font-family: var(--serif); font-size: 1.9rem; color: var(--ink); font-weight: 600; margin-bottom: 10px; }
.ask-hero-sub { font-size: 0.90rem; color: var(--ink-faint); max-width: 440px; margin: 0 auto; line-height: 1.5; }
.chip-btn button {
    background: var(--bg-raised) !important; color: var(--ink-soft) !important;
    border: 1px solid var(--line) !important; border-radius: 20px !important;
    font-size: 0.78rem !important; font-weight: 500 !important; padding: 6px 14px !important;
}
.chip-btn button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }
/* Conversation */
.msg-user { display: flex; justify-content: flex-end; margin-bottom: 22px; }
.msg-user-bubble {
    background: var(--accent-soft); color: var(--ink); padding: 9px 15px; border-radius: 14px 14px 2px 14px;
    max-width: 72%; font-size: 0.90rem; line-height: 1.5;
}
.msg-assistant { margin-bottom: 26px; }
.msg-label { font-family: var(--sans); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--sage); margin-bottom: 6px; }
.msg-body { font-family: var(--serif); font-size: 1.02rem; line-height: 1.65; color: var(--ink); border-left: 2px solid var(--line); padding-left: 14px; }
.msg-meta { display: flex; gap: 14px; align-items: center; margin-top: 10px; padding-left: 16px; font-size: 0.74rem; color: var(--ink-faint); }
.msg-meta .grounded { color: var(--sage); font-weight: 600; }
.msg-sources { margin-top: 8px; padding-left: 16px; display: flex; flex-wrap: wrap; gap: 6px; }
.src-tag {
    font-size: 0.70rem; font-weight: 500; color: var(--ink-soft);
    background: var(--bg-raised); border: 1px solid var(--line); border-radius: 20px; padding: 2px 10px;
}
/* Cards / blocks */
.paper-block { background: var(--bg-raised); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; margin-bottom: 14px; }
.section-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-faint); margin-bottom: 10px; }
/* Source list rows (Library / Connect pages) */
.source-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--line-soft); }
.source-row:last-child { border-bottom: none; }
.source-name { font-weight: 600; font-size: 0.88rem; color: var(--ink); }
.source-meta { font-size: 0.74rem; color: var(--ink-faint); margin-top: 2px; }
/* Insights stat strip */
.stat-strip { display: flex; border: 1px solid var(--line); border-radius: 10px; background: var(--bg-raised); margin-bottom: 18px; overflow: hidden; }
.stat-cell { flex: 1; padding: 16px 18px; border-right: 1px solid var(--line-soft); }
.stat-cell:last-child { border-right: none; }
.stat-num { font-family: var(--serif); font-size: 1.55rem; font-weight: 700; color: var(--ink); }
.stat-lbl { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink-faint); margin-top: 3px; }
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 9px; }
.bar-label { font-size: 0.78rem; color: var(--ink-soft); width: 130px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 8px; background: var(--line-soft); border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; }
.bar-pct { font-size: 0.76rem; color: var(--ink-faint); width: 34px; text-align: right; flex-shrink: 0; }
.status-row { display: flex; align-items: center; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--line-soft); font-size: 0.84rem; }
.status-row:last-child { border-bottom: none; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--sage); display: inline-block; margin-right: 8px; }
.status-dot.down { background: var(--ink-faint); }
/* Widget overrides */
[data-testid="stChatInput"] { background: var(--bg) !important; }
[data-testid="stChatInput"] textarea {
    background: var(--bg-raised) !important; color: var(--ink) !important; border: 1px solid var(--line) !important;
    font-family: var(--sans) !important;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stFileUploader section {
    background: var(--bg-raised) !important; color: var(--ink) !important; border-color: var(--line) !important;
}
.stDataFrame { background: var(--bg-raised) !important; }
.stButton button { border-radius: 8px; font-family: var(--sans); }
.stSlider label, .stSelectbox label, .stTextInput label { color: var(--ink-soft) !important; font-weight: 600 !important; font-size: 0.82rem !important; }
hr { border-color: var(--line) !important; }
.quire-footer { text-align: center; font-size: 0.72rem; color: var(--ink-faint); padding: 30px 0 10px 0; }
</style>"""
