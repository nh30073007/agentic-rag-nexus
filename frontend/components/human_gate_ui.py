import streamlit as st
from utils.api_client import approve_answer

def render_human_gate():
    score = st.session_state.get("pending_score", 0)
    answer = st.session_state.get("pending_answer", "")
    feedback = st.session_state.get("pending_feedback", "")

    st.markdown("**QUALITY CHECK GATE**")
    st.write(f"CRITIC SCORE: {score}/10")

    if score >= 8:
        st.write("STATUS: EXCELLENT")
    elif score >= 6:
        st.write("STATUS: ACCEPTABLE")
    else:
        st.write("STATUS: NEEDS WORK")

    with st.expander("REVIEW GENERATED ANSWER"):
        st.write(answer if answer else "[ NO PREVIEW ]")
        if feedback:
            st.write(f"SYSTEM FEEDBACK: {feedback}")

    user_feedback = st.text_area("YOUR FEEDBACK (OPTIONAL)", key="human_feedback")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("APPROVE AND DELIVER", use_container_width=True):
            result = approve_answer(
                st.session_state.session_id,
                "approved",
                user_feedback
            )
            final = result.get("final_answer", answer) if result else answer
            st.session_state.messages.append({
                "role": "assistant",
                "content": final,
            })
            st.session_state.human_gate_active = False
            st.session_state.human_gate_resolved = False
            st.rerun()

    with c2:
        if st.button("REJECT AND RETRY", use_container_width=True):
            if not user_feedback.strip():
                st.warning("FEEDBACK REQUIRED FOR REJECTION")
            else:
                approve_answer(
                    st.session_state.session_id,
                    "rejected",
                    user_feedback
                )
                st.session_state.human_gate_active = False
                st.session_state.human_gate_resolved = False
                st.session_state.processing = True
                st.rerun()