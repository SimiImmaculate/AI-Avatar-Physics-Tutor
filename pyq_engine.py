import json
from pathlib import Path


BASE_DIR = Path(__file__).parent

PYQ_PAGE_FILE = (
    BASE_DIR
    / "data"
    / "pyq_pages"
    / "pyq_pages.jsonl"
)


def load_pyq_pages():
    if not PYQ_PAGE_FILE.exists():
        return []

    records = []

    with open(
        PYQ_PAGE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                records.append(
                    json.loads(line)
                )
            except json.JSONDecodeError:
                continue

    return records


def get_available_years(
    class_name=None,
    exam_type=None
):
    pages = load_pyq_pages()

    years = set()

    for page in pages:

        if (
            class_name
            and page["class"] != class_name
        ):
            continue

        if (
            exam_type
            and page["exam_type"] != exam_type
        ):
            continue

        if page["year"]:
            years.add(
                page["year"]
            )

    return sorted(
        years,
        reverse=True
    )


def get_available_papers(
    class_name=None,
    exam_type=None
):
    pages = load_pyq_pages()

    papers = {}

    for page in pages:

        if (
            class_name
            and page["class"] != class_name
        ):
            continue

        if (
            exam_type
            and page["exam_type"] != exam_type
        ):
            continue

        key = (
            page["class"],
            page["year"],
            page["exam_type"],
            page["source_file"]
        )

        papers[key] = {
            "class": page["class"],
            "year": page["year"],
            "exam_type": page["exam_type"],
            "source_file": page["source_file"]
        }

    return list(
        papers.values()
    )


def get_paper_pages(
    class_name,
    year,
    exam_type="Public Exam"
):
    pages = load_pyq_pages()

    return [
        page
        for page in pages
        if (
            page["class"] == class_name
            and page["year"] == year
            and page["exam_type"] == exam_type
        )
    ]


def search_pyq_pages(
    query,
    class_name=None,
    year=None,
    exam_type=None,
    limit=10
):
    pages = load_pyq_pages()

    query_terms = {
        term.lower()
        for term in query.split()
        if len(term) >= 2
    }

    scored = []

    for page in pages:

        if (
            class_name
            and page["class"] != class_name
        ):
            continue

        if (
            year
            and page["year"] != year
        ):
            continue

        if (
            exam_type
            and page["exam_type"] != exam_type
        ):
            continue

        text = page["text"].lower()

        score = sum(
            1
            for term in query_terms
            if term in text
        )

        if score > 0:

            scored.append(
                (
                    score,
                    page
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        page
        for _, page in scored[:limit]
    ]


if __name__ == "__main__":

    print(
        "Available XI Public Exam years:"
    )

    print(
        get_available_years(
            "XI",
            "Public Exam"
        )
    )

    print()

    print(
        "Available XII Public Exam years:"
    )

    print(
        get_available_years(
            "XII",
            "Public Exam"
        )
    )