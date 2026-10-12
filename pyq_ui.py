import re
import json
import html
import streamlit as st
from pathlib import Path

from pyq_engine import get_available_years
from pyq_answer_engine import answer_pyq
from pyq_mapping_engine import (
    normalize_class_name,
    get_mapping
)
from voice_engine import generate_speech

from pyq_explanation_engine import generate_explanation

from pyq_mastery_engine import (
    record_pyq_attempt,
    get_overall_stats,
    get_weak_topics
)


BASE_DIR = Path(__file__).parent

PYQ_PATH = (
    BASE_DIR
    / "data"
    / "pyq_questions"
    / "pyq_questions.json"
)


# ============================================================
# LOAD PYQ DATABASE
# ============================================================

def load_pyq_questions():

    if not PYQ_PATH.exists():
        return []

    try:

        with open(
            PYQ_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            if "questions" in data:
                return data["questions"]

        return []

    except Exception:

        return []


# ============================================================
# GET QUESTIONS
# ============================================================

def get_questions(
    class_name,
    year
):

    questions = load_pyq_questions()

    result = []

    requested_class = normalize_class_name(
        class_name
    )

    try:
        requested_year = int(year)
    except (TypeError, ValueError):
        return []

    for q in questions:

        q_class = normalize_class_name(
            q.get("class", "")
        )

        try:

            q_year = int(
                q.get("year")
            )

        except (TypeError, ValueError):

            continue

        if (
            q_class == requested_class
            and q_year == requested_year
        ):

            result.append(q)

    result.sort(
        key=lambda q: int(
            q.get(
                "question_number",
                999
            )
        )
    )

    return result


# ============================================================
# FIND QUESTION
# ============================================================

def find_selected_question(
    questions,
    question_number
):

    for q in questions:

        try:

            if int(
                q.get("question_number")
            ) == int(question_number):

                return q

        except (TypeError, ValueError):

            continue

    return None


# ============================================================
# DISPLAY MAPPING
# ============================================================

def render_mapping_card(
    class_name,
    year,
    question_number
):

    mapping = get_mapping(
        class_name,
        year,
        question_number
    )

    if not mapping:

        return None

    unit = mapping.get(
        "unit",
        "Unknown"
    )

    unit_title = mapping.get(
        "unit_title",
        ""
    )

    topic = mapping.get(
        "topic",
        "General concept"
    )

    confidence = mapping.get(
        "confidence",
        0
    )

    pages = mapping.get(
        "textbook_pages",
        []
    )

    matched_terms = mapping.get(
        "matched_terms",
        []
    )

    confidence_percent = (
        float(confidence) * 100
    )

    st.html(
        f"""
        <div style="
            border:1px solid #bfdbfe;
            border-radius:16px;
            padding:18px;
            margin-top:12px;
            margin-bottom:18px;
            background:linear-gradient(
                135deg,
                #eff6ff,
                #f8fafc
            );
        ">

            <div style="
                font-size:14px;
                font-weight:700;
                color:#1d4ed8;
                margin-bottom:8px;
            ">
                🎯 VERIFIED PYQ TEXTBOOK MAPPING
            </div>

            <div style="
                font-size:18px;
                font-weight:700;
                color:#111827;
            ">
                {html.escape(str(unit))}
                — {html.escape(str(unit_title))}
            </div>

            <div style="
                margin-top:8px;
                color:#475569;
            ">
                <b>Topic:</b>
                {html.escape(str(topic))}
            </div>

            <div style="
                margin-top:5px;
                color:#475569;
            ">
                <b>Mapping Confidence:</b>
                {confidence_percent:.1f}%
            </div>

            <div style="
                margin-top:5px;
                color:#475569;
            ">
                <b>Textbook Pages:</b>
                {html.escape(str(pages))}
            </div>

        </div>
        """,
    )

    return mapping


# ============================================================
# MAIN PYQ PRACTICE UI
# ============================================================


def normalize_pyq_latex(text):
    """
    Convert common LaTeX delimiters returned by the AI
    into Streamlit-compatible math delimiters.
    """

    if not text:
        return ""

    text = str(text)

    # Display math
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.S)

    # Inline math
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.S)

    return text


def render_pyq_practice():

    # ========================================================
    # HEADER
    # ========================================================

    st.html(
        """
        <div style="
            padding:20px;
            border-radius:18px;
            background:linear-gradient(135deg,#111827,#1e3a5f);
            color:white;
            margin-bottom:20px;
        ">
            <h2 style="margin:0;">📚 PYQ Practice</h2>
            <p style="margin:7px 0 0 0;">
                Practice Tamil Nadu State Board Physics Previous Year Questions
                with AI-powered textbook explanations.
            </p>
        </div>
        """
    )

    # ========================================================
    # CLASS
    # ========================================================

    class_name = st.selectbox(
        "🎓 Select Class",
        ["XI", "XII"],
        key="pyq_class"
    )

    # ========================================================
    # YEARS
    # ========================================================

    years = get_available_years(
        class_name
    )

    if not years:

        st.warning(
            "No PYQ years are available for this class."
        )

        return

    year = st.selectbox(
        "📅 Select Year",
        years,
        key="pyq_year"
    )

    # ========================================================
    # QUESTIONS
    # ========================================================

    questions = get_questions(
        class_name=class_name,
        year=year
    )

    if not questions:

        st.warning(
            f"No questions found for "
            f"Class {class_name}, {year}."
        )

        return

    # ========================================================
    # DATABASE STATUS
    # ========================================================

    st.caption(
        f"✅ {len(questions)} questions loaded "
        f"for Class {class_name} — {year}"
    )

    # ========================================================
    # QUESTION SELECTOR
    # ========================================================

    question_numbers = [
        q.get("question_number")
        for q in questions
    ]

    selected_number = st.selectbox(
        "📝 Select Question",
        question_numbers,
        key="pyq_question_number"
    )

    question = find_selected_question(
        questions,
        selected_number
    )

    if question is None:

        st.error(
            "Question could not be loaded."
        )

        return

    # ========================================================
    # QUESTION INFORMATION
    # ========================================================

    marks = question.get(
        "marks",
        ""
    )

    question_type = question.get(
        "question_type",
        ""
    )

    part = question.get(
        "part",
        ""
    )

    question_text = question.get(
        "question",
        ""
    )

    safe_question = html.escape(
        str(question_text)
    )

    st.html(
        f"""
        <div style="
            border:1px solid #d1d5db;
            border-radius:16px;
            padding:20px;
            margin-top:15px;
            margin-bottom:15px;
            background:#f8fafc;
        ">

            <div style="
                font-size:14px;
                color:#64748b;
                margin-bottom:10px;
            ">
                Class {class_name}
                &nbsp;•&nbsp;
                {year}
                &nbsp;•&nbsp;
                Question {selected_number}
                &nbsp;•&nbsp;
                {marks} Marks
                &nbsp;•&nbsp;
                {question_type}
            </div>

            <div style="
                font-size:20px;
                font-weight:600;
                line-height:1.6;
                color:#111827;
            ">
                {question.get("question", "")}
            </div>

        </div>
        """
    )

    # ========================================================
    # OPTIONS
    # ========================================================

    options = question.get(
        "options",
        []
    )

    if options:

        st.markdown(
            "### 🔘 Options"
        )

        for option in options:

            st.html(
                f"""
                <div style="
                    padding:11px 14px;
                    margin:6px 0;
                    border-radius:10px;
                    background:#eef2ff;
                    border:1px solid #c7d2fe;
                    color:#111827;
                ">
                    {option}
                </div>
                """
            )

    # ========================================================
    # VERIFIED MAPPING SUMMARY
    # ========================================================

    mapping = render_mapping_card(
        class_name,
        year,
        selected_number
    )


    if mapping:

        mapping_unit_title = mapping.get(
            "unit_title",
            mapping.get("unit", "Unknown Unit")
        )

        mapping_topic = mapping.get(
            "topic",
            "Physics"
        )

        mapping_confidence = float(
            mapping.get("confidence", 0)
        )

        mapping_pages = mapping.get(
            "textbook_pages",
            []
        )

        safe_mapping_unit = html.escape(
            str(mapping_unit_title)
        )

        safe_mapping_topic = html.escape(
            str(mapping_topic)
        )

        safe_mapping_pages = html.escape(
            str(mapping_pages)
        )

        st.html(
            f"""
            <div style="
                margin-top:16px;
                padding:20px;
                border-radius:18px;
                background:linear-gradient(
                    135deg,
                    #0f172a,
                    #172554
                );
                color:white;
                border:1px solid #334155;
                box-shadow:0 8px 24px rgba(0,0,0,0.18);
            ">

                <div style="
                    font-size:13px;
                    font-weight:800;
                    color:#60a5fa;
                    letter-spacing:0.4px;
                    margin-bottom:10px;
                ">
                    🎯 VERIFIED PYQ → TEXTBOOK CONNECTION
                </div>

                <div style="
                    font-size:21px;
                    font-weight:750;
                    margin-bottom:8px;
                ">
                    {safe_mapping_unit}
                </div>

                <div style="
                    margin-top:8px;
                    color:#cbd5e1;
                    font-size:15px;
                ">
                    <b>Concept:</b> {safe_mapping_topic}
                </div>

                <div style="
                    margin-top:7px;
                    color:#cbd5e1;
                    font-size:15px;
                ">
                    <b>Mapping Confidence:</b>
                    {mapping_confidence * 100:.1f}%
                </div>

                <div style="
                    margin-top:7px;
                    color:#cbd5e1;
                    font-size:15px;
                ">
                    <b>Textbook Pages:</b>
                    {safe_mapping_pages}
                </div>

            </div>
            """
        )

    # ========================================================
    # LANGUAGE
    # ========================================================

    language = st.selectbox(
        "🌐 Explanation Language",
        [
            "English",
            "Tamil",
            "English + Tamil"
        ],
        key="pyq_language"
    )

    # ========================================================
    # AI ANSWER
    # ========================================================

    if st.button(
        "🤖 Explain with Physics Mentor AI",
        type="primary",
        use_container_width=True,
        key="pyq_explain_button"
    ):

        with st.spinner(
            "Physics Mentor AI is reading the "
            "mapped official textbook section..."
        ):

            try:

                result = answer_pyq(
                    class_name=class_name,
                    year=year,
                    question_number=selected_number,
                    language=language
                )

            except Exception as e:

                result = {
                    "success": False,
                    "error": str(e)
                }

        if not result.get("success"):

            st.error(
                result.get(
                    "error",
                    "Unable to generate answer."
                )
            )

            return

        st.session_state[
            "pyq_answer_result"
        ] = result

        st.session_state[
            "pyq_answer_key"
        ] = (
            class_name,
            year,
            selected_number,
            language
        )

    # ========================================================
    # DISPLAY ANSWER
    # ========================================================

    result = st.session_state.get(
        "pyq_answer_result"
    )

    answer_key = st.session_state.get(
        "pyq_answer_key"
    )

    current_key = (
        class_name,
        year,
        selected_number,
        language
    )

    if (
        result
        and answer_key == current_key
    ):

        st.markdown(
            "## 🧠 Physics Mentor AI — Answer"
        )

        # ====================================================
        # ANSWER
        # ====================================================

        answer_text = result.get(
            "answer",
            ""
        )

        # Render AI answer as Markdown so mathematical
        # expressions are displayed properly.
        with st.container(border=True):

            st.markdown(
                "🧠 **PHYSICS MENTOR AI — DETAILED EXPLANATION**"
            )

            st.markdown(
                normalize_pyq_latex(answer_text)
            )


        # ====================================================
        # MAPPED INFORMATION
        # ====================================================

        result_mapping = result.get(
            "mapping"
        )

        if result_mapping:

            st.markdown(
                "### 🎯 PYQ Mapping"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Unit",
                    result_mapping.get(
                        "unit",
                        "—"
                    )
                )

            with col2:

                st.metric(
                    "Topic",
                    result_mapping.get(
                        "topic",
                        "—"
                    )
                )

            with col3:

                confidence = result_mapping.get(
                    "confidence",
                    0
                )

                st.metric(
                    "Confidence",
                    f"{float(confidence) * 100:.1f}%"
                )

        # ====================================================
        # TEXTBOOK SOURCE
        # ====================================================

        pages = result.get(
            "pages",
            []
        )

        if pages:

            st.success(
                "📖 Official Textbook Source — "
                "Tamil Nadu State Board Physics "
                f"• Page(s): {pages}"
            )

        units = []

        if result.get("unit_title"):

            units.append(
                result.get(
                    "unit_title"
                )
            )

        elif result.get("unit"):

            units.append(
                result.get(
                    "unit"
                )
            )

        if units:

            st.caption(
                "📚 Textbook Unit: "
                + " • ".join(
                    str(x)
                    for x in units
                )
            )

        topic = result.get(
            "topic"
        )

        if topic:

            st.caption(
                f"🎯 Topic: {topic}"
            )

        if result.get(
            "cached"
        ):

            st.caption(
                "⚡ Answer loaded from AI answer cache."
            )

        # ====================================================
        # DETAILED EXAM-READY EXPLANATION
        # ====================================================

        explanation_key = f"{class_name}_{year}_{selected_number}_{language}"

        if st.button(
            "📘 Generate Detailed Step-by-Step Explanation",
            use_container_width=True,
            key=f"pyq_detailed_explanation_{class_name}_{year}_{selected_number}_{language}"
        ):
            with st.spinner("Building the detailed exam-ready explanation from the textbook-grounded answer..."):
                try:
                    detailed_result = generate_explanation(
                        class_name=class_name,
                        year=year,
                        question_number=selected_number,
                        language=language
                    )
                    st.session_state["pyq_explanation_result"] = detailed_result
                    st.session_state["pyq_explanation_key"] = explanation_key
                except Exception as e:
                    st.error(f"Detailed explanation generation failed: {e}")

        detailed_result = st.session_state.get("pyq_explanation_result")
        detailed_result_key = st.session_state.get("pyq_explanation_key")
        if detailed_result and detailed_result_key == explanation_key:
            if detailed_result.get("success"):
                st.markdown("### 📝 Detailed Exam-Ready Solution")
                st.markdown(
                    normalize_pyq_latex(detailed_result.get("explanation", ""))
                )
            else:
                st.warning(detailed_result.get("error", "Detailed explanation is unavailable."))

        # ====================================================
        # VOICE
        # ====================================================

        st.markdown(
            "### 🔊 Listen to the Explanation"
        )

        if st.button(
            "▶️ Generate Voice",
            key=(
                f"pyq_voice_"
                f"{class_name}_"
                f"{year}_"
                f"{selected_number}_"
                f"{language}"
            )
        ):

            with st.spinner(
                "Generating explanation audio..."
            ):

                try:

                    speech_language = (
                        "Tamil"
                        if language == "Tamil"
                        else "English"
                    )

                    voice_text = result.get(
                        "answer",
                        ""
                    )

                    stored_explanation = st.session_state.get(
                        "pyq_explanation_result"
                    )

                    stored_explanation_key = st.session_state.get(
                        "pyq_explanation_key"
                    )

                    if (
                        stored_explanation
                        and stored_explanation_key
                        == f"{class_name}_{year}_{selected_number}_{language}"
                        and stored_explanation.get("success")
                    ):

                        voice_text = stored_explanation.get(
                            "explanation",
                            voice_text
                        )

                    audio_path = generate_speech(
                        voice_text,
                        language=speech_language
                    )

                    with open(
                        audio_path,
                        "rb"
                    ) as audio_file:

                        st.audio(
                            audio_file.read(),
                            format="audio/wav"
                        )

                except Exception as e:

                    st.error(
                        f"Voice generation failed: {e}"
                    )

        # ====================================================
        # PRACTICE AGAIN
        # ====================================================

        st.markdown(
            "### 🎯 Keep Practising"
        )

        st.info(
            "Try another question from the same "
            "year or switch to another year to "
            "compare how the topic is asked in "
            "previous examinations."
        )