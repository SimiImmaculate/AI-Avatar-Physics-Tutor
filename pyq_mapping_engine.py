import json
from pathlib import Path
from functools import lru_cache


BASE_DIR = Path(__file__).parent

MAPPING_PATH = (
    BASE_DIR
    / "data"
    / "pyq_questions"
    / "pyq_mapping.json"
)


def normalize_class_name(class_name):
    """
    Convert different class formats into XI / XII.
    """

    value = str(class_name).strip().upper()

    if value in {"XI", "11", "CLASS XI", "CLASS 11"}:
        return "XI"

    if value in {"XII", "12", "CLASS XII", "CLASS 12"}:
        return "XII"

    return value


@lru_cache(maxsize=1)
def load_mapping():

    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"PYQ mapping file not found: {MAPPING_PATH}"
        )

    with open(
        MAPPING_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if isinstance(data, dict):

        # Support mapping stored directly by ID.
        if "mappings" in data:
            data = data["mappings"]

        elif "questions" in data:
            data = data["questions"]

    return data


def get_mapping(
    class_name,
    year,
    question_number
):
    """
    Return the V2 textbook mapping for one PYQ.
    """

    class_name = normalize_class_name(class_name)
    year = int(year)
    question_number = int(question_number)

    data = load_mapping()

    target_id = (
        f"{class_name}_{year}_Q{question_number}"
    )

    # Dictionary format
    if isinstance(data, dict):

        if target_id in data:
            return data[target_id]

        # Some formats may use a list inside the dictionary.
        values = data.values()

    else:
        values = data

    # List format
    for item in values:

        if not isinstance(item, dict):
            continue

        item_id = item.get("id")

        if item_id == target_id:
            return item

        try:
            item_class = normalize_class_name(
                item.get("class", "")
            )

            item_year = int(item.get("year"))

            item_question = int(
                item.get("question_number")
            )

        except (TypeError, ValueError):
            continue

        if (
            item_class == class_name
            and item_year == year
            and item_question == question_number
        ):
            return item

    return None


def get_mapping_summary(
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

    return {
        "id": mapping.get("id"),
        "unit": mapping.get("unit"),
        "unit_title": mapping.get("unit_title"),
        "volume": mapping.get("volume"),
        "topic": mapping.get("topic"),
        "confidence": mapping.get("confidence"),
        "textbook_pages": mapping.get(
            "textbook_pages",
            []
        ),
        "matched_terms": mapping.get(
            "matched_terms",
            []
        )
    }


if __name__ == "__main__":

    print("=" * 70)
    print("PYQ MAPPING ENGINE TEST")
    print("=" * 70)

    tests = [
        ("XII", 2026, 20),
        ("XII", 2026, 7),
        ("XII", 2026, 8),
        ("XI", 2024, 4),
    ]

    for class_name, year, question_number in tests:

        mapping = get_mapping(
            class_name,
            year,
            question_number
        )

        print()
        print(
            f"{class_name} {year} Q{question_number}"
        )

        if mapping:

            print(
                "Unit:",
                mapping.get("unit")
            )

            print(
                "Topic:",
                mapping.get("topic")
            )

            print(
                "Confidence:",
                mapping.get("confidence")
            )

            print(
                "Pages:",
                mapping.get("textbook_pages")
            )

        else:

            print("Mapping NOT FOUND")