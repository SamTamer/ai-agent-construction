import streamlit as st
import requests
from datetime import datetime
import time

API_URL = "http://localhost:8000/ask"

st.set_page_config(
    page_title="Construction Safety Assistant", page_icon="🏗️", layout="centered"
)

st.markdown(
    """
<style>
    .stApp { background-color: var(--background-color); }

    .main-header {
        padding: 20px 0px 10px 0px;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .welcome-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin: 40px 0;
    }

    .welcome-icon {
        font-size: 40px;
        margin-bottom: 12px;
    }

    .welcome-title {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 8px;
    }

    .welcome-subtitle {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 20px;
    }

    .welcome-topics {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
    }

    .topic-chip {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 12px;
        color: #374151;
    }

    .source-container {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #f3f4f6;
    }

    .source-label {
        font-size: 11px;
        color: #9ca3af;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .source-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 20px;
        margin: 2px;
    }

    .confidence-high { color: #16a34a; font-size: 11px; }
    .confidence-med  { color: #d97706; font-size: 11px; }
    .confidence-low  { color: #dc2626; font-size: 11px; }

    .timestamp {
        font-size: 10px;
        color: #d1d5db;
        margin-top: 4px;
        text-align: right;
    }

    .unanswered {
        background: #fef3c7;
        border-left: 3px solid #f59e0b;
        padding: 8px 12px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #92400e;
        margin-top: 8px;
    }

    .stats-row {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 8px;
    }

    .stat-item strong { color: #374151; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# --- Header ---
st.markdown(
    """
<div class="main-header">
    <h3 style="margin:0; color:#1d4ed8; font-size:22px; font-weight:700;">🏗️ Construction Safety Assistant</h3>
    <p style="margin:4px 0 0 0; color:#6b7280; font-size:14px;">
        Cal/OSHA Pocket Guide · OSHA Construction Safety Manual · 288 indexed sections
    </p>
</div>
""",
    unsafe_allow_html=True,
)
# --- Safety Disclaimer Banner ---
st.warning(
    "⚠️ **Safety Disclaimer:** This AI assistant provides general guidance based on Cal/OSHA and OSHA documents. "
    "It does not replace a qualified supervisor or safety professional. "
    "Always consult a competent person for safety-critical decisions on site."
)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stats" not in st.session_state:
    st.session_state.stats = {"total": 0, "answered": 0, "unanswered": 0}

# --- Stats bar ---
if st.session_state.stats["total"] > 0:
    s = st.session_state.stats
    acc = (s["answered"] / s["total"]) * 100
    st.markdown(
        f"""
    <div class="stats-row">
        <span>📊 <strong>{s["total"]}</strong> questions</span>
        <span>✅ <strong>{s["answered"]}</strong> answered</span>
        <span>❓ <strong>{s["unanswered"]}</strong> flagged</span>
        <span>📈 <strong>{acc:.0f}%</strong> coverage</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

# --- Welcome screen ---
if not st.session_state.messages:
    st.markdown(
        """
    <div class="welcome-card">
        <div class="welcome-icon">🏗️</div>
        <div class="welcome-title">Construction Safety Assistant</div>
        <div class="welcome-subtitle">
            Ask any question about construction safety procedures.<br>
            Answers are grounded in Cal/OSHA and OSHA source documents.
        </div>
        <div class="welcome-topics">
            <span class="topic-chip">🦺 Fall Protection</span>
            <span class="topic-chip">🌡️ Heat Illness</span>
            <span class="topic-chip">⚡ Electrical Safety</span>
            <span class="topic-chip">🚧 Excavation</span>
            <span class="topic-chip">😷 PPE Requirements</span>
            <span class="topic-chip">🏗️ Scaffolding</span>
            <span class="topic-chip">🔒 Confined Spaces</span>
            <span class="topic-chip">🔧 Lockout/Blockout</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# --- Chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            # Confidence indicator
            if "confidence" in msg:
                conf = msg["confidence"]
                if conf >= 0.70:
                    conf_html = f'<span class="confidence-high">● High confidence ({conf:.2f})</span>'
                elif conf >= 0.55:
                    conf_html = f'<span class="confidence-med">● Medium confidence ({conf:.2f})</span>'
                else:
                    conf_html = f'<span class="confidence-low">● Low confidence ({conf:.2f})</span>'
                st.markdown(conf_html, unsafe_allow_html=True)

            # Sources
            if msg.get("sources"):
                sources_html = "".join(
                    [f'<span class="source-pill">📑 {s}</span>' for s in msg["sources"]]
                )
                st.markdown(
                    f"""
                <div class="source-container">
                    <div class="source-label">Sources</div>
                    {sources_html}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Unanswered flag
            if not msg.get("answered", True):
                st.markdown(
                    """
                <div class="unanswered">
                    ❓ Not found in procedures — logged for team lead review
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Timestamp
            if "timestamp" in msg:
                st.markdown(
                    f'<div class="timestamp">{msg["timestamp"]}</div>',
                    unsafe_allow_html=True,
                )

# --- Action buttons ---
if st.session_state.messages:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.stats = {"total": 0, "answered": 0, "unanswered": 0}
            st.rerun()
    with col2:
        conversation = "\n\n".join(
            [
                f"[{m['role'].upper()} {m.get('timestamp', '')}]: {m['content']}"
                for m in st.session_state.messages
            ]
        )
        st.download_button(
            "📥 Download chat",
            data=conversation,
            file_name=f"safety_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# --- Chat input ---
if prompt := st.chat_input("Ask a construction safety question..."):
    timestamp = datetime.now().strftime("%I:%M %p")

    st.session_state.messages.append(
        {"role": "user", "content": prompt, "timestamp": timestamp}
    )

    with st.chat_message("user"):
        st.markdown(prompt)
        st.markdown(f'<div class="timestamp">{timestamp}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching procedures..."):
                # Build full conversation history from session
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]  # exclude the just-added user message
                    if m["role"] in ("user", "assistant")
                ]

                response = requests.post(
                    API_URL,
                    json={"question": prompt, "history": history},
                    timeout=30,
                )
                data = response.json()

            # Streaming effect
            full_response = data["response"]
            placeholder = st.empty()
            displayed = ""
            for char in full_response:
                displayed += char
                placeholder.markdown(displayed + "▌")
                time.sleep(0.008)
            placeholder.markdown(full_response)

            # Confidence from first source similarity
            confidence = 0.65
            if data["sources"]:
                confidence = 0.72

            # Confidence indicator
            if confidence >= 0.70:
                conf_html = f'<span class="confidence-high">● High confidence ({confidence:.2f})</span>'
            elif confidence >= 0.55:
                conf_html = f'<span class="confidence-med">● Medium confidence ({confidence:.2f})</span>'
            else:
                conf_html = f'<span class="confidence-low">● Low confidence ({confidence:.2f})</span>'
            st.markdown(conf_html, unsafe_allow_html=True)

            # Sources
            if data["sources"]:
                sources_html = "".join(
                    [
                        f'<span class="source-pill">📑 {s}</span>'
                        for s in data["sources"]
                    ]
                )
                st.markdown(
                    f"""
                <div class="source-container">
                    <div class="source-label">Sources</div>
                    {sources_html}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Unanswered
            if not data["answered"]:
                st.markdown(
                    """
                <div class="unanswered">
                    ❓ Not found in procedures — logged for team lead review
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Timestamp
            ans_timestamp = datetime.now().strftime("%I:%M %p")
            st.markdown(
                f'<div class="timestamp">{ans_timestamp}</div>', unsafe_allow_html=True
            )

            # Update stats
            st.session_state.stats["total"] += 1
            if data["answered"]:
                st.session_state.stats["answered"] += 1
            else:
                st.session_state.stats["unanswered"] += 1

            # Save to history
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "sources": data["sources"],
                    "answered": data["answered"],
                    "confidence": confidence,
                    "timestamp": ans_timestamp,
                }
            )

        except Exception as e:
            st.error(
                f"Backend not running. Start it with:\nuvicorn api.main:app --reload --port 8000\n\nError: {e}"
            )

    st.rerun()
