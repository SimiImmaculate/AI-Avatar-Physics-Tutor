import json
from pathlib import Path
from datetime import datetime


# =========================================================
# PROGRESS FILE
# =========================================================

BASE_DIR = Path(__file__).parent

PROGRESS_DIR = BASE_DIR / "data"

PROGRESS_FILE = PROGRESS_DIR / "student_progress.json"


# =========================================================
# DEFAULT PROGRESS
# =========================================================

def default_progress():
    return {
        "total_quizzes": 0,
        "total_questions": 0,
        "total_correct": 0,
        "modules": {},
        "quiz_history": []
    }


# =========================================================
# LOAD PROGRESS
# =========================================================

def load_progress():
    from app_config import use_session_storage

    if use_session_storage():
        import streamlit as st
        if "_physics_progress" not in st.session_state:
            st.session_state["_physics_progress"] = default_progress()
        return st.session_state["_physics_progress"]

    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    if not PROGRESS_FILE.exists():
        progress = default_progress()
        save_progress(progress)
        return progress

    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
            progress = json.load(file)
    except (json.JSONDecodeError, OSError):
        progress = default_progress()

    return progress


def save_progress(progress):
    from app_config import use_session_storage

    if use_session_storage():
        import copy
        import streamlit as st
        st.session_state["_physics_progress"] = copy.deepcopy(progress)
        return

    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(progress, file, indent=2, ensure_ascii=False)


def record_quiz_result(
    class_name,
    volume,
    unit_name,
    score,
    total_questions,
    history
):

    progress = load_progress()

    correct = score

    accuracy = (
        (correct / total_questions) * 100
        if total_questions > 0
        else 0
    )

    module_key = (
        f"{class_name} | "
        f"{volume} | "
        f"{unit_name}"
    )

    # -----------------------------------------------------
    # Create module if necessary
    # -----------------------------------------------------

    if module_key not in progress["modules"]:

        progress["modules"][module_key] = {
            "class": class_name,
            "volume": volume,
            "unit": unit_name,
            "quizzes": 0,
            "questions": 0,
            "correct": 0,
            "accuracy": 0,
            "last_score": 0,
            "last_accuracy": 0,
            "last_updated": ""
        }

    module = progress["modules"][module_key]

    # -----------------------------------------------------
    # Update module
    # -----------------------------------------------------

    module["quizzes"] += 1

    module["questions"] += total_questions

    module["correct"] += correct

    module["accuracy"] = (
        module["correct"]
        / module["questions"]
    ) * 100

    module["last_score"] = score

    module["last_accuracy"] = accuracy

    module["last_updated"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # -----------------------------------------------------
    # Update overall statistics
    # -----------------------------------------------------

    progress["total_quizzes"] += 1

    progress["total_questions"] += total_questions

    progress["total_correct"] += correct

    # -----------------------------------------------------
    # Save individual quiz
    # -----------------------------------------------------

    progress["quiz_history"].append(
        {
            "date": datetime.now().isoformat(
                timespec="seconds"
            ),
            "class": class_name,
            "volume": volume,
            "unit": unit_name,
            "score": score,
            "total": total_questions,
            "accuracy": accuracy,
            "history": history
        }
    )

    # Keep the history manageable
    progress["quiz_history"] = (
        progress["quiz_history"][-50:]
    )

    save_progress(progress)

    return progress


# =========================================================
# OVERALL ACCURACY
# =========================================================

def get_overall_accuracy(progress):

    if progress["total_questions"] == 0:

        return 0

    return (
        progress["total_correct"]
        / progress["total_questions"]
    ) * 100


# =========================================================
# MODULE LEVEL
# =========================================================

def get_module_level(accuracy):

    if accuracy >= 90:

        return "Advanced"

    if accuracy >= 75:

        return "Strong"

    if accuracy >= 60:

        return "Developing"

    return "Needs Practice"


# =========================================================
# MODULE SUMMARY
# =========================================================

def get_module_summaries(progress):

    summaries = []

    for module in progress["modules"].values():

        summaries.append(
            {
                **module,
                "level": get_module_level(
                    module["accuracy"]
                )
            }
        )

    summaries.sort(
        key=lambda item: item["accuracy"],
        reverse=True
    )

    return summaries