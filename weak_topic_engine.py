from progress_engine import (
    load_progress,
    get_module_summaries
)


# =========================================================
# FIND WEAKEST TOPIC
# =========================================================

def get_weakest_topic():

    progress = load_progress()

    modules = get_module_summaries(progress)

    if not modules:
        return None

    # Lowest accuracy = highest practice priority
    weakest = min(
        modules,
        key=lambda item: item["accuracy"]
    )

    return weakest


# =========================================================
# GET PRACTICE RECOMMENDATION
# =========================================================

def get_practice_recommendation():

    weakest = get_weakest_topic()

    if weakest is None:

        return {
            "available": False,
            "message": (
                "Complete at least one adaptive quiz "
                "to identify a weak topic."
            )
        }

    accuracy = weakest["accuracy"]

    if accuracy < 50:

        message = (
            f"Let's strengthen your foundation in "
            f"{weakest['unit']}."
        )

    elif accuracy < 75:

        message = (
            f"You are developing in "
            f"{weakest['unit']}. "
            f"A little more practice will improve your confidence."
        )

    else:

        message = (
            f"{weakest['unit']} is currently your "
            f"lowest-scoring topic. "
            f"Let's make it stronger."
        )

    return {
        "available": True,
        "class": weakest["class"],
        "volume": weakest["volume"],
        "unit": weakest["unit"],
        "accuracy": accuracy,
        "level": weakest["level"],
        "message": message
    }