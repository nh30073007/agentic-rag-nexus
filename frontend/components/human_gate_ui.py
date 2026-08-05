"""Clean human approval UI."""

import streamlit as st

from frontend.utils.api_client import approve_answer


def render_human_gate(session_id, answer_preview, critique_score, critique_feedback):
    if critique_score >= 8:
        score_color = "#22c55e"
        score_label = "Excellent"
    elif critique_score >= 6:
        score_color = "#eab308"
        score_label = "Good"
    else:
        score_color = "#ef4444"
        score_label = "Needs Work"

    st.markdown(f"""
        <div style="
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 16px;
            padding: 1.2rem;
            margin: 0.8rem 0;
        ">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                <span style="font-size: 1.2rem;">🛑</span>
                <span style="font-size: 1rem; font-weight: 700; color: #f5f5f5;">Human Approval Required</span>
            </div>
            <div style="display: flex; gap: 0.8rem; margin-bottom: 1rem;">
                <div style="flex: 1; background: #141414; border-radius: 10px; padding: 0.8rem; text-align: center; border: 1px solid #2a2a2a;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: {score_color};">{critique_score}</div>
                    <div style="font-size: 0.7rem; color: #737373; margin-top: 0.2rem;">Critic Score / 10</div>
                </div>
                <div style="flex: 1; background: #141414; border-radius: 10px; padding: 0.8rem; text-align: center; border: 1px solid #2a2a2a; display: flex; align-items: center; justify-content: center;">
                    <div style="font-size: 0.85rem; font-weight: 600; color: {score_color};">{score_label}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Review Generated Answer", expanded=True):
        st.markdown(f"""
            <div style="
                background: #141414;
                border-radius: 10px;
                padding: 1rem;
                border: 1px solid #262626;
                color: #d4d4d4;
                font-size: 0.9rem;
                line-height: 1.7;
            ">{answer_preview[:2000].replace(chr(10), '<br>')}</div>
        """, unsafe_allow_html=True)

        if critique_feedback:
            st.markdown(f"""
                <div style="
                    margin-top: 0.8rem;
                    padding: 0.6rem 0.8rem;
                    background: rgba(234, 179, 8, 0.08);
                    border-left: 3px solid #eab308;
                    border-radius: 0 8px 8px 0;
                    color: #eab308;
                    font-size: 0.8rem;
                ">
                    <strong>🛡️ Critic Feedback:</strong><br>{critique_feedback}
                </div>
            """, unsafe_allow_html=True)

    feedback = st.text_area(
        "💬 Your Feedback (optional)",
        placeholder="e.g., Add more technical details...",
        key=f"feedback_{session_id}",
        label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Approve & Deliver", type="primary", use_container_width=True):
            _handle_approval(session_id, feedback)

    with c2:
        if st.button("❌ Reject & Retry", use_container_width=True):
            _handle_rejection(session_id, feedback)


def _handle_approval(session_id, feedback):
    with st.spinner("Finalizing..."):
        result = approve_answer(session_id, "approved", feedback)
        if "error" not in result:
            final = result.get("final_answer", "")
            st.session_state.messages.append({
                "role": "assistant",
                "content": final,
                "sources": [],
            })
            st.session_state.human_gate_active = False
            st.session_state.human_gate_resolved = False
            st.success("✅ Approved!")
            st.rerun()
        else:
            st.error(f"Failed: {result.get('error')}")


def _handle_rejection(session_id, feedback):
    if not feedback.strip():
        st.warning("Please provide feedback for improvement!")
        return

    with st.spinner("Retrying..."):
        result = approve_answer(session_id, "rejected", feedback)
        if "error" not in result:
            st.session_state.human_gate_active = False
            st.session_state.human_gate_resolved = False
            st.session_state.processing = True
            st.info("♻️ Retrying with feedback...")
            st.rerun()
        else:
            st.error(f"Failed: {result.get('error')}")