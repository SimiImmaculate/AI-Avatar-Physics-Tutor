import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
PROGRESS_FILE = DATA_DIR / "student_progress.json"
PYQ_MASTERY_FILE = DATA_DIR / "pyq_mastery.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_mastery():
    from app_config import use_session_storage

    if use_session_storage():
        import streamlit as st
        if "_physics_pyq_mastery" not in st.session_state:
            st.session_state["_physics_pyq_mastery"] = {
                "total_attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "by_class": {},
                "by_unit": {},
                "by_topic": {},
                "recent_attempts": [],
            }
        return st.session_state["_physics_pyq_mastery"]

    if not PYQ_MASTERY_FILE.exists():
        return {
            "total_attempts": 0,
            "correct": 0,
            "incorrect": 0,
            "by_class": {},
            "by_unit": {},
            "by_topic": {},
            "recent_attempts": [],
        }

    try:
        with open(PYQ_MASTERY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "total_attempts": 0,
            "correct": 0,
            "incorrect": 0,
            "by_class": {},
            "by_unit": {},
            "by_topic": {},
            "recent_attempts": [],
        }


def save_mastery(data):
    from app_config import use_session_storage

    if use_session_storage():
        import copy
        import streamlit as st
        st.session_state["_physics_pyq_mastery"] = copy.deepcopy(data)
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PYQ_MASTERY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_pyq_attempt(
    class_name,
    year,
    question_number,
    unit,
    topic,
    correct
):

    data = load_mastery()

    data["total_attempts"] += 1

    if correct:
        data["correct"] += 1
    else:
        data["incorrect"] += 1


    # --------------------------------------------------------
    # CLASS
    # --------------------------------------------------------

    class_key = str(class_name)

    if class_key not in data["by_class"]:
        data["by_class"][class_key] = {
            "attempts": 0,
            "correct": 0
        }

    data["by_class"][class_key]["attempts"] += 1

    if correct:
        data["by_class"][class_key]["correct"] += 1


    # --------------------------------------------------------
    # UNIT
    # --------------------------------------------------------

    unit_key = f"{class_name} — {unit}"

    if unit_key not in data["by_unit"]:
        data["by_unit"][unit_key] = {
            "attempts": 0,
            "correct": 0,
            "topic": topic
        }

    data["by_unit"][unit_key]["attempts"] += 1

    if correct:
        data["by_unit"][unit_key]["correct"] += 1


    # --------------------------------------------------------
    # TOPIC
    # --------------------------------------------------------

    topic_key = f"{class_name} — {topic}"

    if topic_key not in data["by_topic"]:
        data["by_topic"][topic_key] = {
            "attempts": 0,
            "correct": 0
        }

    data["by_topic"][topic_key]["attempts"] += 1

    if correct:
        data["by_topic"][topic_key]["correct"] += 1


    # --------------------------------------------------------
    # RECENT ATTEMPTS
    # --------------------------------------------------------

    data["recent_attempts"].insert(
        0,
        {
            "class": class_name,
            "year": year,
            "question_number": question_number,
            "unit": unit,
            "topic": topic,
            "correct": correct,
            "timestamp": datetime.now().isoformat()
        }
    )

    data["recent_attempts"] = data["recent_attempts"][:20]

    save_mastery(data)

    return data


def calculate_accuracy(correct, attempts):

    if attempts == 0:
        return 0.0

    return round(
        (correct / attempts) * 100,
        1
    )


def get_overall_stats():

    data = load_mastery()

    attempts = data["total_attempts"]
    correct = data["correct"]

    return {
        "attempts": attempts,
        "correct": correct,
        "incorrect": data["incorrect"],
        "accuracy": calculate_accuracy(
            correct,
            attempts
        )
    }


def get_weak_topics(limit=5, threshold=70.0):

    data = load_mastery()

    topics = []

    for topic, stats in data["by_topic"].items():

        attempts = stats["attempts"]

        if attempts == 0:
            continue

        accuracy = calculate_accuracy(
            stats["correct"],
            attempts
        )

        # Only topics below the mastery threshold
        # are considered weak.
        if accuracy >= threshold:
            continue

        topics.append(
            {
                "topic": topic,
                "attempts": attempts,
                "correct": stats["correct"],
                "accuracy": accuracy
            }
        )

    topics.sort(
        key=lambda x: (
            x["accuracy"],
            -x["attempts"]
        )
    )

    return topics[:limit]