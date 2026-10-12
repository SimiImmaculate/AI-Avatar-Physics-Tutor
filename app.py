from pathlib import Path
import re

import streamlit as st

from tutor_engine import ask_physics_tutor
from voice_engine import transcribe_audio, generate_speech
from avatar_engine import get_avatar_state
from pyq_ui import render_pyq_practice
from textbook_diagram_engine import search_textbook_diagrams, render_diagram_results

from quiz_engine import (
    generate_quiz_bank,
    choose_next_question,
    get_next_difficulty
)

from progress_engine import (
    load_progress,
    record_quiz_result,
    get_overall_accuracy,
    get_module_summaries
)

from weak_topic_engine import (
    get_practice_recommendation
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Physics Mentor AI",
    page_icon="⚛️",
    layout="wide"
)


# =========================================================
# AVATAR DISPLAY
# =========================================================

def show_avatar(state="idle"):

    avatar = get_avatar_state(state)

    html = f"""
    <div style="
        width: 100%;
        box-sizing: border-box;
        padding: 20px;
        border-radius: 22px;
        background: linear-gradient(135deg, #182848, #4b6cb7);
        text-align: center;
        margin: 10px 0 24px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    ">

        <div style="
            font-size: 64px;
            line-height: 1.1;
        ">
            {avatar["emoji"]}
        </div>

        <div style="
            font-size: 24px;
            font-weight: 700;
            margin-top: 8px;
        ">
            {avatar["title"]}
        </div>

        <div style="
            font-size: 15px;
            margin-top: 6px;
            opacity: 0.9;
        ">
            {avatar["message"]}
        </div>

    </div>
    """

    st.html(html)


# =========================================================
# SESSION STATE
# =========================================================

# ---------------------------------------------------------
# Tutor state
# ---------------------------------------------------------

if "tutor_result" not in st.session_state:
    st.session_state.tutor_result = None

if "voice_question" not in st.session_state:
    st.session_state.voice_question = ""

if "voice_audio_path" not in st.session_state:
    st.session_state.voice_audio_path = None

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

if "question_input" not in st.session_state:
    st.session_state.question_input = ""


# ---------------------------------------------------------
# Avatar state
# ---------------------------------------------------------

if "avatar_state" not in st.session_state:
    st.session_state.avatar_state = "idle"


# ---------------------------------------------------------
# Weak-topic practice state
# ---------------------------------------------------------

if "practice_weak_topic" not in st.session_state:
    st.session_state.practice_weak_topic = False

if "auto_start_weak_quiz" not in st.session_state:
    st.session_state.auto_start_weak_quiz = False

if "practice_class" not in st.session_state:
    st.session_state.practice_class = None

if "practice_volume" not in st.session_state:
    st.session_state.practice_volume = None

if "practice_unit" not in st.session_state:
    st.session_state.practice_unit = None


# =========================================================
# QUIZ SESSION STATE
# =========================================================

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_used_ids" not in st.session_state:
    st.session_state.quiz_used_ids = []

if "quiz_current_question" not in st.session_state:
    st.session_state.quiz_current_question = None

if "quiz_current_difficulty" not in st.session_state:
    st.session_state.quiz_current_difficulty = "medium"

if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

if "quiz_question_number" not in st.session_state:
    st.session_state.quiz_question_number = 0

if "quiz_answered" not in st.session_state:
    st.session_state.quiz_answered = False

if "quiz_selected_option" not in st.session_state:
    st.session_state.quiz_selected_option = None

if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []

if "quiz_source_pages" not in st.session_state:
    st.session_state.quiz_source_pages = []

if "quiz_source_file" not in st.session_state:
    st.session_state.quiz_source_file = ""

if "quiz_progress_saved" not in st.session_state:
    st.session_state.quiz_progress_saved = False


# ---------------------------------------------------------
# Active quiz target
# ---------------------------------------------------------

if "quiz_target_class" not in st.session_state:
    st.session_state.quiz_target_class = None

if "quiz_target_volume" not in st.session_state:
    st.session_state.quiz_target_volume = None

if "quiz_target_unit_number" not in st.session_state:
    st.session_state.quiz_target_unit_number = None

if "quiz_target_unit_name" not in st.session_state:
    st.session_state.quiz_target_unit_name = None


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = Path(__file__).parent


def normalize_learning_math(text):
    """Normalize common LaTeX delimiters for Streamlit Markdown."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.S)
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.S)
    return text


# =========================================================
# TITLE
# =========================================================

st.title("⚛️ Physics Mentor AI")

st.subheader(
    "Your Multilingual AI Physics Tutor"
)

st.write(
    "Learn Physics through simple explanations, "
    "step-by-step problem solving and textbook-grounded answers."
)


# =========================================================
# DETERMINE AVATAR DISPLAY STATE
# =========================================================

display_avatar_state = st.session_state.avatar_state

if (
    st.session_state.quiz_current_question is not None
    and display_avatar_state == "idle"
):

    if (
        st.session_state.quiz_progress_saved
        and st.session_state.quiz_answered
        and st.session_state.quiz_question_number >= 4
    ):
        display_avatar_state = "success"

    else:
        display_avatar_state = "quiz"


show_avatar(display_avatar_state)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📚 Tutor Learning Settings")


class_name = st.sidebar.selectbox(
    "Class",
    ["XI", "XII"]
)


volume = st.sidebar.selectbox(
    "Volume",
    ["Volume I", "Volume II"]
)


# =========================================================
# UNIT OPTIONS
# =========================================================

if class_name == "XI" and volume == "Volume I":

    units = {
        "Unit I – Nature of Physical World and Measurement": 1,
        "Unit II – Kinematics": 2,
        "Unit III – Laws of Motion": 3,
        "Unit IV – Work, Energy and Power": 4,
        "Unit V – Motion of System of Particles and Rigid Bodies": 5,
    }

elif class_name == "XI" and volume == "Volume II":

    units = {
        "Unit VI – Gravitation": 6,
        "Unit VII – Properties of Matter": 7,
        "Unit VIII – Heat and Thermodynamics": 8,
        "Unit IX – Kinetic Theory of Gases": 9,
        "Unit X – Oscillations": 10,
        "Unit XI – Waves": 11,
    }

elif class_name == "XII" and volume == "Volume I":

    units = {
        "Unit I – Electrostatics": 1,
        "Unit II – Current Electricity": 2,
        "Unit III – Magnetism": 3,
        "Unit IV – Electromagnetic Induction and Alternating Current": 4,
        "Unit V – Electromagnetic Waves": 5,
    }

else:

    units = {
        "Unit VI – Ray Optics": 6,
        "Unit VII – Wave Optics": 7,
        "Unit VIII – Dual Nature of Radiation and Matter": 8,
        "Unit IX – Atomic and Nuclear Physics": 9,
        "Unit X – Electronics and Communication": 10,
        "Unit XI – Recent Developments in Physics": 11,
    }


selected_unit = st.sidebar.selectbox(
    "Unit",
    list(units.keys())
)

unit_number = units[selected_unit]


# =========================================================
# LANGUAGE
# =========================================================

language = st.sidebar.selectbox(
    "Language",
    [
        "English",
        "Tamil",
        "English + Tamil"
    ]
)


# =========================================================
# CURRENT MODULE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.info(
    f"📚 **Current Tutor Module**\n\n"
    f"Class: {class_name}\n\n"
    f"{volume}\n\n"
    f"{selected_unit}"
)


# =========================================================
# VOICE INPUT
# =========================================================

st.markdown("### 🎤 Or ask using your voice")

st.caption(
    "Record a short Physics question in English, Tamil, "
    "or English + Tamil."
)


audio_input = st.audio_input(
    "🎤 Record your Physics question"
)


# =========================================================
# TRANSCRIBE VOICE
# =========================================================

if audio_input is not None:

    if st.button(
        "🔄 Convert Voice to Question",
        use_container_width=True
    ):

        st.session_state.avatar_state = "listening"

        with st.spinner(
            "🎤 Listening and converting your speech..."
        ):

            try:

                transcription = transcribe_audio(
                    audio_input.getvalue(),
                    language
                )

                transcript = transcription["transcript"].strip()

                st.session_state.voice_question = transcript

                st.session_state.question_input = transcript

                st.success(
                    "Voice converted successfully."
                )

                st.session_state.avatar_state = "idle"

            except Exception as e:

                st.session_state.avatar_state = "idle"

                st.error(
                    f"Speech recognition error:\n\n{e}"
                )


# =========================================================
# QUESTION INPUT
# =========================================================

st.markdown("### 🎓 Ask your Physics Tutor")


question = st.text_area(
    "Enter your Physics question:",
    key="question_input",
    height=160,
    placeholder=(
        "Example:\n"
        "What is acceleration and what is its SI unit?\n\n"
        "Or:\n"
        "A body starts from rest with an acceleration "
        "of 2 m/s². Find its velocity after 5 seconds."
    )
)


# =========================================================
# SHOW TRANSCRIPTION
# =========================================================

if st.session_state.voice_question:

    st.markdown("#### 📝 Transcribed Question")

    st.info(
        st.session_state.voice_question
    )


# =========================================================
# ASK PHYSICS MENTOR
# =========================================================

if st.button(
    "🚀 Ask Physics Mentor",
    use_container_width=True
):

    question = st.session_state.question_input.strip()

    if not question:

        st.warning(
            "Please enter or record a Physics question."
        )

    else:

        st.session_state.avatar_state = "thinking"

        with st.spinner(
            "⚛️ Physics Mentor is thinking..."
        ):

            try:

                result = ask_physics_tutor(
                    class_name=class_name,
                    volume=volume,
                    unit_number=unit_number,
                    question=question,
                    language=language
                )

                st.session_state.tutor_result = result

                st.session_state.avatar_state = "speaking"

                st.session_state.last_question = question

                st.session_state.voice_audio_path = None

            except Exception as e:

                st.session_state.avatar_state = "idle"

                st.error(
                    f"Physics Mentor encountered an error:\n\n{e}"
                )


# =========================================================
# DISPLAY TUTOR ANSWER
# =========================================================

if st.session_state.tutor_result is not None:

    result = st.session_state.tutor_result

    st.markdown(
        "## 👨‍🏫 Physics Mentor's Explanation"
    )

    st.markdown(
        normalize_learning_math(result["answer"])
    )


    # =====================================================
    # VOICE OUTPUT
    # =====================================================

    st.markdown("---")

    st.markdown(
        "## 🔊 Listen to the Explanation"
    )


    if st.button(
        "🔊 Generate Voice Explanation",
        use_container_width=True
    ):

        st.session_state.avatar_state = "speaking"

        answer_text = result["answer"]

        with st.spinner(
            "🔊 Generating voice explanation..."
        ):

            try:

                speech_text = re.sub(
                    r"[\*\_#\`]",
                    "",
                    answer_text
                )

                speech_text = speech_text.replace(
                    "•",
                    ""
                )

                audio_path = generate_speech(
                    speech_text,
                    language=language
                )

                st.session_state.voice_audio_path = audio_path

                st.success(
                    "🔊 Voice explanation generated successfully!"
                )

            except Exception as e:

                st.error(
                    f"Voice generation failed:\n\n{e}"
                )


    # =====================================================
    # PLAY GENERATED AUDIO
    # =====================================================

    if st.session_state.voice_audio_path:

        st.audio(
            st.session_state.voice_audio_path,
            format="audio/wav"
        )


    # =====================================================
    # SOURCE INFORMATION
    # =====================================================

    st.markdown("---")

    st.markdown(
        "### 📚 Textbook Source"
    )

    st.write(
        f"**Class:** {class_name}"
    )

    st.write(
        f"**Volume:** {volume}"
    )

    st.write(
        f"**Unit:** {selected_unit}"
    )

    st.write(
        f"**Textbook pages used:** {result['pages']}"
    )


    # =====================================================
    # SOURCE FILE
    # =====================================================

    with st.expander(
        "🔎 View source file"
    ):

        st.code(
            result["source_file"],
            language="text"
        )



# =========================================================
# TEXTBOOK DIAGRAM SEARCH
# =========================================================

st.markdown("---")
st.markdown("## 🖼️ Textbook Diagrams and Figures")
st.caption(
    "Search the indexed textbook pages for relevant figures. "
    "Candidate pages are not treated as verified until visually checked."
)

diagram_query = st.text_input(
    "Search for a diagram or concept",
    value=selected_unit.split("–", 1)[-1].strip(),
    key="textbook_diagram_query",
    placeholder="Examples: free body diagram, ray diagram, vernier caliper",
)

diagram_limit = st.selectbox(
    "Number of candidate pages",
    [3, 5, 8],
    index=1,
    key="textbook_diagram_limit",
)

if st.button("🔎 Find Textbook Figures", key="find_textbook_figures"):
    try:
        matches = search_textbook_diagrams(
            query=diagram_query,
            class_name=class_name,
            volume=volume,
            limit=diagram_limit,
        )
        render_diagram_results(matches)
    except Exception as exc:
        st.error(f"Textbook figure search failed: {exc}")


# =========================================================
# DETERMINE QUIZ TARGET
# =========================================================

quiz_class = class_name
quiz_volume = volume
quiz_unit_number = unit_number
quiz_unit_name = selected_unit


# ---------------------------------------------------------
# Weak-topic override
# ---------------------------------------------------------

if st.session_state.get(
    "practice_weak_topic",
    False
):

    practice_class = st.session_state.get(
        "practice_class"
    )

    practice_volume = st.session_state.get(
        "practice_volume"
    )

    practice_unit = st.session_state.get(
        "practice_unit"
    )

    if (
        practice_class
        and practice_volume
        and practice_unit
    ):

        quiz_class = practice_class

        quiz_volume = practice_volume

        quiz_unit_name = practice_unit

        unit_match = re.search(
            r"Unit\s+([IVX]+)",
            practice_unit
        )

        if unit_match:

            roman = unit_match.group(1)

            roman_values = {
                "I": 1,
                "II": 2,
                "III": 3,
                "IV": 4,
                "V": 5,
                "VI": 6,
                "VII": 7,
                "VIII": 8,
                "IX": 9,
                "X": 10,
                "XI": 11
            }

            quiz_unit_number = roman_values.get(
                roman,
                unit_number
            )


# =========================================================
# ADAPTIVE PHYSICS QUIZ
# =========================================================

st.markdown("---")

st.markdown("## 🧠 Adaptive Physics Quiz")

st.caption(
    "Test your understanding with textbook-grounded questions. "
    "Your next question becomes easier or harder based on your answer."
)


# =========================================================
# ACTIVE QUIZ TARGET DISPLAY
# =========================================================

if st.session_state.quiz_current_question is not None:

    active_class = (
        st.session_state.quiz_target_class
        or quiz_class
    )

    active_volume = (
        st.session_state.quiz_target_volume
        or quiz_volume
    )

    active_unit = (
        st.session_state.quiz_target_unit_name
        or quiz_unit_name
    )

    st.info(
        f"🎯 **Active Quiz Topic:** "
        f"{active_class} • {active_volume} • {active_unit}"
    )


# =========================================================
# AUTOMATIC WEAK-TOPIC QUIZ FLAG
# =========================================================

auto_start_weak_quiz = st.session_state.get(
    "auto_start_weak_quiz",
    False
)


# =========================================================
# START / RESET QUIZ
# =========================================================

start_quiz_clicked = st.button(
    "🚀 Start New Adaptive Quiz",
    use_container_width=True
)


if start_quiz_clicked or auto_start_weak_quiz:

    st.session_state.avatar_state = "thinking"

    with st.spinner(
        "🧠 Preparing your personalized Physics quiz..."
    ):

        try:

            # -------------------------------------------------
            # Save exact quiz target
            # -------------------------------------------------

            st.session_state.quiz_target_class = quiz_class

            st.session_state.quiz_target_volume = quiz_volume

            st.session_state.quiz_target_unit_number = (
                quiz_unit_number
            )

            st.session_state.quiz_target_unit_name = (
                quiz_unit_name
            )

            # Prevent repeated automatic generation
            st.session_state.auto_start_weak_quiz = False


            # -------------------------------------------------
            # Generate quiz
            #
            # IMPORTANT:
            # Positional arguments are intentionally used here.
            # This avoids the "unexpected keyword argument
            # 'quiz_class'" error.
            # -------------------------------------------------

            quiz_data = generate_quiz_bank(
                quiz_class,
                quiz_volume,
                quiz_unit_number
            )


            # -------------------------------------------------
            # Reset quiz state
            # -------------------------------------------------

            st.session_state.quiz_questions = (
                quiz_data["questions"]
            )

            st.session_state.quiz_used_ids = []

            st.session_state.quiz_current_difficulty = (
                "medium"
            )

            st.session_state.quiz_score = 0

            st.session_state.quiz_question_number = 0

            st.session_state.quiz_answered = False

            st.session_state.quiz_selected_option = None

            st.session_state.quiz_history = []

            st.session_state.quiz_progress_saved = False

            st.session_state.quiz_source_pages = (
                quiz_data["source_pages"]
            )

            st.session_state.quiz_source_file = (
                quiz_data["source_file"]
            )


            # -------------------------------------------------
            # Select first question
            # -------------------------------------------------

            first_question = choose_next_question(
                st.session_state.quiz_questions,
                [],
                "medium"
            )

            st.session_state.quiz_current_question = (
                first_question
            )


            # -------------------------------------------------
            # Clear weak-topic selection
            #
            # The actual target is already stored in
            # quiz_target_*.
            # -------------------------------------------------

            st.session_state.practice_weak_topic = False


            # -------------------------------------------------
            # Quiz is active
            # -------------------------------------------------

            st.session_state.avatar_state = "quiz"

            st.success(
                "🎯 Your adaptive quiz is ready!"
            )

        except Exception as e:

            st.session_state.avatar_state = "idle"

            # Make sure automatic mode does not get stuck
            st.session_state.auto_start_weak_quiz = False

            st.error(
                f"Quiz generation failed:\n\n{e}"
            )


# =========================================================
# QUIZ DISPLAY
# =========================================================

if st.session_state.quiz_current_question:

    if not (
        st.session_state.quiz_progress_saved
        and st.session_state.quiz_answered
        and st.session_state.quiz_question_number >= 4
    ):

        st.session_state.avatar_state = "quiz"


    quiz_question = (
        st.session_state.quiz_current_question
    )

    question_number = (
        st.session_state.quiz_question_number + 1
    )


    # -----------------------------------------------------
    # Progress
    # -----------------------------------------------------

    st.progress(
        min(
            st.session_state.quiz_question_number / 5,
            1.0
        )
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Question",
            f"{question_number}/5"
        )


    with col2:

        st.metric(
            "Score",
            st.session_state.quiz_score
        )


    with col3:

        st.metric(
            "Difficulty",
            quiz_question["difficulty"].title()
        )


    # -----------------------------------------------------
    # Question
    # -----------------------------------------------------

    st.markdown(
        f"### Q{question_number}. "
        f"{quiz_question['question']}"
    )

    st.caption(
        f"Question type: "
        f"{quiz_question['type'].title()}"
    )


    # -----------------------------------------------------
    # Options
    # -----------------------------------------------------

    option_labels = [
        "A",
        "B",
        "C",
        "D"
    ]

    options = quiz_question["options"]

    selected_option = st.radio(
        "Choose your answer:",
        options=[
            f"{option_labels[i]}. {options[i]}"
            for i in range(4)
        ],
        key=f"quiz_option_{quiz_question['id']}"
    )


    # -----------------------------------------------------
    # Submit Answer
    # -----------------------------------------------------

    if not st.session_state.quiz_answered:

        if st.button(
            "✅ Submit Answer",
            use_container_width=True
        ):

            selected_index = next(
                i
                for i, option in enumerate(options)
                if selected_option == (
                    f"{option_labels[i]}. {option}"
                )
            )

            correct_index = (
                quiz_question["correct_option"]
            )

            is_correct = (
                selected_index == correct_index
            )


            if is_correct:

                st.session_state.quiz_score += 1


            # -------------------------------------------------
            # Save history
            # -------------------------------------------------

            st.session_state.quiz_history.append(
                {
                    "question_id": quiz_question["id"],
                    "difficulty": quiz_question["difficulty"],
                    "question": quiz_question["question"],
                    "selected_option": selected_index,
                    "correct_option": correct_index,
                    "correct": is_correct
                }
            )


            st.session_state.quiz_selected_option = (
                selected_index
            )

            st.session_state.quiz_answered = True


            # -------------------------------------------------
            # Adapt next difficulty
            # -------------------------------------------------

            st.session_state.quiz_current_difficulty = (
                get_next_difficulty(
                    quiz_question["difficulty"],
                    is_correct
                )
            )


            st.rerun()


    # -----------------------------------------------------
    # Answer Feedback
    # -----------------------------------------------------

    if st.session_state.quiz_answered:

        selected_index = (
            st.session_state.quiz_selected_option
        )

        correct_index = (
            quiz_question["correct_option"]
        )


        if selected_index == correct_index:

            st.success(
                "🎉 Correct! Excellent work."
            )

        else:

            st.error(
                "❌ Not quite. Let's learn from it."
            )

            st.info(
                f"Correct answer: "
                f"{option_labels[correct_index]}. "
                f"{options[correct_index]}"
            )


        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        st.markdown("### 💡 Explanation")

        st.markdown(
            normalize_learning_math(quiz_question["explanation"])
        )


        # -------------------------------------------------
        # Adaptive message
        # -------------------------------------------------

        if selected_index == correct_index:

            if quiz_question["difficulty"] == "hard":

                st.info(
                    "🔥 Great! You handled a hard question. "
                    "The next question will remain challenging."
                )

            else:

                st.info(
                    "📈 You're doing well. "
                    "The next question will become harder."
                )

        else:

            if quiz_question["difficulty"] == "easy":

                st.info(
                    "🌱 Keep learning. "
                    "We'll reinforce the fundamentals."
                )

            else:

                st.info(
                    "💪 Don't worry. "
                    "The next question will be easier so you "
                    "can strengthen the concept."
                )


        # -------------------------------------------------
        # Next Question
        # -------------------------------------------------

        if question_number < 5:

            if st.button(
                "➡️ Next Question",
                use_container_width=True
            ):

                st.session_state.quiz_used_ids.append(
                    quiz_question["id"]
                )


                next_question = choose_next_question(
                    st.session_state.quiz_questions,
                    st.session_state.quiz_used_ids,
                    st.session_state.quiz_current_difficulty
                )


                st.session_state.quiz_current_question = (
                    next_question
                )

                st.session_state.quiz_question_number += 1

                st.session_state.quiz_answered = False

                st.session_state.quiz_selected_option = None

                st.session_state.avatar_state = "quiz"

                st.rerun()


        else:

            # =================================================
            # SAVE COMPLETED QUIZ
            # =================================================

            if not st.session_state.quiz_progress_saved:

                try:

                    saved_class = (
                        st.session_state.quiz_target_class
                        or quiz_class
                    )

                    saved_volume = (
                        st.session_state.quiz_target_volume
                        or quiz_volume
                    )

                    saved_unit = (
                        st.session_state.quiz_target_unit_name
                        or quiz_unit_name
                    )


                    record_quiz_result(
                        class_name=saved_class,
                        volume=saved_volume,
                        unit_name=saved_unit,
                        score=st.session_state.quiz_score,
                        total_questions=5,
                        history=st.session_state.quiz_history
                    )


                    st.session_state.quiz_progress_saved = True

                    st.session_state.avatar_state = "success"


                except Exception as e:

                    st.warning(
                        f"Progress could not be saved: {e}"
                    )


            # =================================================
            # FINAL RESULT
            # =================================================

            st.markdown("---")

            st.markdown(
                "## 🏆 Quiz Completed!"
            )


            score = st.session_state.quiz_score

            percentage = (
                score / 5
            ) * 100


            st.metric(
                "Final Score",
                f"{score}/5"
            )


            st.metric(
                "Accuracy",
                f"{percentage:.0f}%"
            )


            if percentage == 100:

                st.success(
                    "🌟 Outstanding! You have mastered "
                    "this topic very well."
                )

            elif percentage >= 80:

                st.success(
                    "👏 Excellent performance! "
                    "You have a strong understanding."
                )

            elif percentage >= 60:

                st.info(
                    "👍 Good effort! "
                    "A little more practice will strengthen "
                    "your understanding."
                )

            else:

                st.warning(
                    "📚 Keep practising. "
                    "Review the textbook concepts and try again."
                )


            # -------------------------------------------------
            # Question Performance
            # -------------------------------------------------

            st.markdown(
                "### 📊 Question Performance"
            )


            for index, item in enumerate(
                st.session_state.quiz_history,
                start=1
            ):

                if item["correct"]:

                    status = "✅ Correct"

                else:

                    status = "❌ Incorrect"


                st.write(
                    f"**Q{index} — "
                    f"{item['difficulty'].title()} — "
                    f"{status}**"
                )


            # -------------------------------------------------
            # Quiz Source
            # -------------------------------------------------

            st.markdown(
                "### 📚 Quiz Source"
            )

            st.write(
                f"**Quiz Topic:** "
                f"{st.session_state.quiz_target_unit_name}"
            )

            st.write(
                f"Textbook pages used: "
                f"{st.session_state.quiz_source_pages}"
            )


            with st.expander(
                "🔎 View quiz source file"
            ):

                st.code(
                    st.session_state.quiz_source_file,
                    language="text"
                )


            st.info(
                "Start a new quiz to practise this topic again."
            )


# =========================================================
# STUDENT PROGRESS DASHBOARD
# =========================================================

st.markdown("---")

st.markdown("## 📊 My Physics Progress")

st.caption(
    "Your learning progress is saved locally and updated "
    "after every completed adaptive quiz."
)


progress_data = load_progress()


overall_accuracy = get_overall_accuracy(
    progress_data
)


module_summaries = get_module_summaries(
    progress_data
)


# =========================================================
# OVERALL METRICS
# =========================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Quizzes Completed",
        progress_data["total_quizzes"]
    )


with col2:

    st.metric(
        "Questions Attempted",
        progress_data["total_questions"]
    )


with col3:

    st.metric(
        "Correct Answers",
        progress_data["total_correct"]
    )


with col4:

    st.metric(
        "Overall Accuracy",
        f"{overall_accuracy:.0f}%"
    )


# =========================================================
# CURRENT MODULE
# =========================================================

current_module_key = (
    f"{class_name} | "
    f"{volume} | "
    f"{selected_unit}"
)


current_module = progress_data[
    "modules"
].get(
    current_module_key
)


if current_module:

    st.markdown(
        "### 📘 📚 Current Tutor Module Performance"
    )


    current_level = (
        "Advanced"
        if current_module["accuracy"] >= 90
        else "Strong"
        if current_module["accuracy"] >= 75
        else "Developing"
        if current_module["accuracy"] >= 60
        else "Needs Practice"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Module Quizzes",
            current_module["quizzes"]
        )


    with col2:

        st.metric(
            "Module Accuracy",
            f"{current_module['accuracy']:.0f}%"
        )


    with col3:

        st.metric(
            "Current Level",
            current_level
        )


    st.progress(
        min(
            current_module["accuracy"] / 100,
            1.0
        )
    )


else:

    st.info(
        "📚 Complete an adaptive quiz for the selected "
        "module to start tracking your progress."
    )



# =========================================================
# FULL SYLLABUS TOPIC PERFORMANCE
# =========================================================

st.markdown("### 📚 Topic Performance")
st.caption(
    "All 22 syllabus units are listed. Scores are shown only "
    "for units with recorded quiz attempts."
)

SYLLABUS_UNITS = [
    ("XI", "Volume I", "Unit I – Nature of Physical World and Measurement"),
    ("XI", "Volume I", "Unit II – Kinematics"),
    ("XI", "Volume I", "Unit III – Laws of Motion"),
    ("XI", "Volume I", "Unit IV – Work, Energy and Power"),
    ("XI", "Volume I", "Unit V – Motion of System of Particles and Rigid Bodies"),
    ("XI", "Volume II", "Unit VI – Gravitation"),
    ("XI", "Volume II", "Unit VII – Properties of Matter"),
    ("XI", "Volume II", "Unit VIII – Heat and Thermodynamics"),
    ("XI", "Volume II", "Unit IX – Kinetic Theory of Gases"),
    ("XI", "Volume II", "Unit X – Oscillations"),
    ("XI", "Volume II", "Unit XI – Waves"),
    ("XII", "Volume I", "Unit I – Electrostatics"),
    ("XII", "Volume I", "Unit II – Current Electricity"),
    ("XII", "Volume I", "Unit III – Magnetism"),
    ("XII", "Volume I", "Unit IV – Electromagnetic Induction and Alternating Current"),
    ("XII", "Volume I", "Unit V – Electromagnetic Waves"),
    ("XII", "Volume II", "Unit VI – Ray Optics"),
    ("XII", "Volume II", "Unit VII – Wave Optics"),
    ("XII", "Volume II", "Unit VIII – Dual Nature of Radiation and Matter"),
    ("XII", "Volume II", "Unit IX – Atomic and Nuclear Physics"),
    ("XII", "Volume II", "Unit X – Electronics and Communication"),
    ("XII", "Volume II", "Unit XI – Recent Developments in Physics"),
]

recorded_modules = progress_data.get("modules", {})
attempted_units = 0

for syllabus_class, syllabus_volume, syllabus_unit in SYLLABUS_UNITS:
    module_key = f"{syllabus_class} | {syllabus_volume} | {syllabus_unit}"
    module = recorded_modules.get(module_key)

    with st.container(border=True):
        st.markdown(f"**{syllabus_class} · {syllabus_volume}**")
        st.write(syllabus_unit)

        if not module:
            st.caption("⚪ Not started — no quiz attempts recorded")
            continue

        attempted_units += 1
        accuracy = float(module.get("accuracy", 0) or 0)
        quiz_count = int(module.get("quizzes", 0) or 0)
        correct = int(module.get("correct", 0) or 0)
        questions = int(module.get("questions", 0) or 0)

        level = (
            "Advanced" if accuracy >= 90 else
            "Strong" if accuracy >= 75 else
            "Developing" if accuracy >= 60 else
            "Needs practice"
        )

        st.progress(max(0.0, min(accuracy / 100, 1.0)))
        st.caption(
            f"🟢 Practised · {accuracy:.0f}% accuracy · "
            f"{quiz_count} quiz(es) · {correct}/{questions} correct · {level}"
        )

# =========================================================
# LEARNING INSIGHTS
# =========================================================

st.markdown("### 🧠 Learning Insights")

attempted_modules = [
    item for item in recorded_modules.values()
    if isinstance(item, dict) and int(item.get("quizzes", 0) or 0) > 0
]

if not attempted_modules:
    st.info(
        "Your learning insights will appear after you complete "
        "your first adaptive quiz. All 22 units are listed above."
    )
else:
    strongest = max(attempted_modules, key=lambda item: float(item.get("accuracy", 0) or 0))
    weakest = min(attempted_modules, key=lambda item: float(item.get("accuracy", 0) or 0))

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Strongest practised topic",
            f"{float(strongest.get('accuracy', 0) or 0):.0f}%",
            help=str(strongest.get("unit", "Topic")),
        )
        st.caption(
            f"{strongest.get('class', '')} · "
            f"{strongest.get('volume', '')} · {strongest.get('unit', '')}"
        )
    with col2:
        st.metric(
            "Topic needing most practice",
            f"{float(weakest.get('accuracy', 0) or 0):.0f}%",
            help=str(weakest.get("unit", "Topic")),
        )
        st.caption(
            f"{weakest.get('class', '')} · "
            f"{weakest.get('volume', '')} · {weakest.get('unit', '')}"
        )

    st.caption(
        f"Progress recorded for {attempted_units} of "
        f"{len(SYLLABUS_UNITS)} syllabus units."
    )

# =========================================================
# RECENT QUIZ HISTORY
# =========================================================

st.markdown("### 🕘 Recent Quiz Attempts")

history = progress_data.get("quiz_history", [])

if not history:
    st.info("No completed quizzes recorded yet.")
else:
    for attempt in reversed(history[-5:]):
        attempt_class = attempt.get("class", "")
        attempt_volume = attempt.get("volume", "")
        attempt_unit = attempt.get("unit", "Physics")
        score = attempt.get("score", 0)
        total = attempt.get("total", 0)
        accuracy = attempt.get("accuracy", 0)
        date = attempt.get("date", "")

        st.write(
            f"**{attempt_class} · {attempt_volume} · {attempt_unit}** — "
            f"{score}/{total} ({float(accuracy or 0):.0f}%)"
        )
        st.caption(date)



# =========================================================
# PYQ PRACTICE
# =========================================================

st.markdown("---")

st.markdown(
    "## 📚 Previous Year Question Practice"
)

st.caption(
    "Practice 494 Tamil Nadu State Board Physics "
    "previous-year questions with textbook-grounded "
    "AI explanations."
)

render_pyq_practice()


# =========================================================
# WEAK TOPIC PRACTICE
# =========================================================

st.markdown("---")

st.markdown(
    "## 🎯 Personalized Overall Learning Practice"
)

st.caption(
    "Physics Mentor AI identifies the topic that needs "
    "the most practice based on your quiz performance."
)


practice = get_practice_recommendation()


if not practice["available"]:

    st.info(
        f"📚 {practice['message']}"
    )

else:

    st.markdown(
        f"### 🎯 Recommended Overall Learning Topic: "
        f"**{practice['unit']}**"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Current Accuracy",
            f"{practice['accuracy']:.0f}%"
        )


    with col2:

        st.metric(
            "Learning Level",
            practice["level"]
        )


    with col3:

        st.metric(
            "Priority",
            "High"
            if practice["accuracy"] < 60
            else "Medium"
        )


    st.info(
        f"💡 {practice['message']}"
    )


    if st.button(
        "🎯 Practice My Weak Topic",
        use_container_width=True
    ):

        # -------------------------------------------------
        # Save weak-topic target
        # -------------------------------------------------

        st.session_state.practice_weak_topic = True

        st.session_state.practice_class = (
            practice["class"]
        )

        st.session_state.practice_volume = (
            practice["volume"]
        )

        st.session_state.practice_unit = (
            practice["unit"]
        )


        # -------------------------------------------------
        # Save quiz target
        # -------------------------------------------------

        st.session_state.quiz_target_class = (
            practice["class"]
        )

        st.session_state.quiz_target_volume = (
            practice["volume"]
        )

        st.session_state.quiz_target_unit_name = (
            practice["unit"]
        )


        # -------------------------------------------------
        # Extract Unit number
        # -------------------------------------------------

        unit_match = re.search(
            r"Unit\s+([IVX]+)",
            practice["unit"]
        )


        if unit_match:

            roman = unit_match.group(1)

            roman_values = {
                "I": 1,
                "II": 2,
                "III": 3,
                "IV": 4,
                "V": 5,
                "VI": 6,
                "VII": 7,
                "VIII": 8,
                "IX": 9,
                "X": 10,
                "XI": 11
            }

            st.session_state.quiz_target_unit_number = (
                roman_values.get(
                    roman,
                    1
                )
            )


        # -------------------------------------------------
        # Avatar
        # -------------------------------------------------

        st.session_state.avatar_state = "quiz"


        # -------------------------------------------------
        # Clear previous quiz
        # -------------------------------------------------

        st.session_state.quiz_questions = []

        st.session_state.quiz_used_ids = []

        st.session_state.quiz_current_question = None

        st.session_state.quiz_score = 0

        st.session_state.quiz_question_number = 0

        st.session_state.quiz_answered = False

        st.session_state.quiz_selected_option = None

        st.session_state.quiz_history = []

        st.session_state.quiz_progress_saved = False


        # -------------------------------------------------
        # Automatically start weak-topic quiz
        # -------------------------------------------------

        st.session_state.auto_start_weak_quiz = True

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Physics Mentor AI • Tamil Nadu State Board Physics • "
    "Textbook-Grounded AI Tutor"
)