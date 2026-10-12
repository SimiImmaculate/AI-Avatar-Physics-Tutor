import streamlit as st
from datetime import datetime


def initialize_fresh_session():

    if "physics_session_initialized" not in st.session_state:

        st.session_state.physics_session_initialized = True

        st.session_state.student_session_started = (
            datetime.now().isoformat()
        )

        # Fresh quiz state
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.quiz_questions = []
        st.session_state.quiz_answers = []
        st.session_state.quiz_score = 0

        # Fresh PYQ state
        st.session_state.pyq_selected_question = None
        st.session_state.pyq_answer_visible = False

        # Fresh weak-topic state
        st.session_state.weak_topic = None
        st.session_state.personalized_practice_started = False

        # Fresh tutor state
        st.session_state.last_tutor_question = ""
        st.session_state.last_tutor_answer = ""

        # Fresh dashboard session
        st.session_state.session_attempts = []
        st.session_state.session_correct = 0
        st.session_state.session_questions = 0


def reset_current_session():

    keys = list(st.session_state.keys())

    for key in keys:
        del st.session_state[key]

    st.rerun()