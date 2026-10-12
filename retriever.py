from pathlib import Path
import re


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# UNIT FILE LOADER
# ============================================================

def load_unit_file(class_name, volume, unit_number):

    class_folder = (
        "class11"
        if class_name == "XI"
        else "class12"
    )

    volume_folder = (
        "volume1"
        if volume == "Volume I"
        else "volume2"
    )

    folder = (
        DATA_DIR
        / class_folder
        / volume_folder
    )

    matching_files = sorted(
        folder.glob(
            f"unit{unit_number:02d}_*.txt"
        )
    )

    if not matching_files:
        return None

    return matching_files[0]


# ============================================================
# PAGE PARSER
# ============================================================

def split_into_pages(text):

    """
    Convert the ingested textbook into individual
    textbook-page chunks.

    Each chunk keeps:
        SOURCE_PAGE
        PDF_PAGE
        textbook content
    """

    pattern = r"------------------------------------------------------------"

    parts = re.split(pattern, text)

    pages = []

    current_source_page = None
    current_pdf_page = None
    current_content = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        source_match = re.search(
            r"SOURCE_PAGE:\s*(\d+)",
            part
        )

        pdf_match = re.search(
            r"PDF_PAGE:\s*(\d+)",
            part
        )

        if source_match and pdf_match:

            if current_source_page is not None:

                content = "\n".join(
                    current_content
                ).strip()

                if content:
                    pages.append({
                        "source_page": current_source_page,
                        "pdf_page": current_pdf_page,
                        "text": content
                    })

            current_source_page = int(
                source_match.group(1)
            )

            current_pdf_page = int(
                pdf_match.group(1)
            )

            current_content = []

        else:

            if current_source_page is not None:
                current_content.append(part)

    # Add final page

    if current_source_page is not None:

        content = "\n".join(
            current_content
        ).strip()

        if content:

            pages.append({
                "source_page": current_source_page,
                "pdf_page": current_pdf_page,
                "text": content
            })

    return pages


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    text = text.lower()

    # Common PDF extraction artefacts
    replacements = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "–": "-",
        "—": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ============================================================
# TOKENIZE
# ============================================================

def tokenize(text):

    text = normalize_text(text)

    return set(
        re.findall(
            r"[a-zA-Z0-9]+",
            text
        )
    )


# ============================================================
# PHYSICS KEYWORDS
# ============================================================

PHYSICS_TERMS = {
    "velocity",
    "speed",
    "acceleration",
    "displacement",
    "distance",
    "motion",
    "relative",
    "projectile",
    "gravity",
    "force",
    "momentum",
    "energy",
    "work",
    "power",
    "torque",
    "angular",
    "rotation",
    "gravitation",
    "pressure",
    "temperature",
    "heat",
    "wave",
    "frequency",
    "oscillation",
    "electric",
    "electricity",
    "charge",
    "current",
    "voltage",
    "resistance",
    "magnetic",
    "induction",
    "optics",
    "lens",
    "mirror",
    "photon",
    "atom",
    "nuclear",
    "semiconductor",
    "equation",
    "formula",
    "derive",
    "calculate",
    "numerical",
    "example",
    "definition",
}


# ============================================================
# SCORE ONE PAGE
# ============================================================

# ============================================================
# SCORE ONE PAGE
# ============================================================

def score_page(page, question):

    question_normalized = normalize_text(question)
    page_text = normalize_text(page["text"])

    # Make whitespace consistent
    question_normalized = re.sub(
        r"\s+",
        " ",
        question_normalized
    )

    page_text = re.sub(
        r"\s+",
        " ",
        page_text
    )

    question_words = tokenize(question_normalized)
    page_words = tokenize(page_text)

    if not question_words:
        return 0

    score = 0

    # ========================================================
    # 1. Basic word overlap
    # ========================================================

    overlap = question_words & page_words

    score += len(overlap) * 2

    # ========================================================
    # 2. Physics terminology
    # ========================================================

    for term in PHYSICS_TERMS:

        if term in question_words and term in page_words:
            score += 4

    # ========================================================
    # 3. Concept-specific intent
    # ========================================================

    # --------------------------------------------------------
    # ACCELERATION + SI UNIT
    # --------------------------------------------------------

    if "si unit" in question_normalized:

        if "si unit" in page_text:
            score += 25

        if "acceleration" in page_text:
            score += 8

        if "rate of change of velocity" in page_text:
            score += 15

        if "dimensional formula" in page_text:
            score += 5

    # --------------------------------------------------------
    # STARTS FROM REST
    # --------------------------------------------------------

    starts_from_rest = (
        "starts from rest" in question_normalized
        or "start from rest" in question_normalized
        or "from rest" in question_normalized
    )

    if starts_from_rest:

        if "suppose the particle starts from rest" in page_text:
            score += 25

        if "starts from rest" in page_text:
            score += 20

        if "u = 0" in page_text:
            score += 18

        if "u 0" in page_text:
            score += 10

        if "initial velocity" in page_text:
            score += 6

    # --------------------------------------------------------
    # FIND VELOCITY AFTER TIME
    # --------------------------------------------------------

    asks_velocity = (
        "find its velocity" in question_normalized
        or "find the velocity" in question_normalized
        or "calculate the velocity" in question_normalized
        or "what is the velocity" in question_normalized
    )

    has_time = (
        "seconds" in question_normalized
        or "second" in question_normalized
        or "after" in question_normalized
    )

    if asks_velocity and has_time:

        # Strongly prefer the fundamental kinematic equation.
        if "kinematic equations" in page_text:
            score += 35

        if "v = u + at" in page_text:
            score += 45

        # PDF extraction can insert spaces between symbols.
        if "v u at" in page_text:
            score += 30

        if "equations of motion" in page_text:
            score += 12

        if "constant acceleration" in page_text:
            score += 12

    # --------------------------------------------------------
    # GENERAL KINEMATIC EQUATION INTENT
    # --------------------------------------------------------

    if (
        "kinematic" in question_normalized
        or "equation of motion" in question_normalized
        or "equations of motion" in question_normalized
    ):

        if "kinematic equations" in page_text:
            score += 25

        if "equations of motion" in page_text:
            score += 15

        if "v = u + at" in page_text:
            score += 25

    # --------------------------------------------------------
    # UNIFORM ACCELERATION
    # --------------------------------------------------------

    if "uniform acceleration" in question_normalized:

        if "uniformly accelerated motion" in page_text:
            score += 20

        if "constant acceleration" in page_text:
            score += 20

    # --------------------------------------------------------
    # AVERAGE ACCELERATION
    # --------------------------------------------------------

    if "average acceleration" in question_normalized:

        if "average acceleration" in page_text:
            score += 30

    # --------------------------------------------------------
    # PROJECTILE INTENT
    # --------------------------------------------------------

    projectile_question = (
        "projectile" in question_normalized
        or "projected" in question_normalized
        or "angle of projection" in question_normalized
        or "horizontal range" in question_normalized
        or "range of the projectile" in question_normalized
    )

    if projectile_question:

        if "projectile motion" in page_text:
            score += 30

        if "projectile" in page_text:
            score += 15

    else:

        # If the student did NOT ask about projectile motion,
        # prevent projectile pages from dominating just because
        # they contain velocity and acceleration.
        if "projectile motion" in page_text:
            score -= 20

        if "2.11.1 introduction" in page_text:
            score -= 15

        if "horizontal projection" in page_text:
            score -= 15

    # ========================================================
    # 4. Numerical-problem intent
    # ========================================================

    numerical_terms = {
        "calculate",
        "find",
        "solve",
        "value",
        "determine",
        "numerical",
        "after",
        "seconds",
        "second"
    }

    if question_words & numerical_terms:

        if "example" in page_text:
            score += 5

        if "solution" in page_text:
            score += 5

        if "equation" in page_text:
            score += 8

        if "kinematic equations" in page_text:
            score += 12

    # ========================================================
    # 5. Exercise-page penalty for conceptual questions
    # ========================================================

    conceptual_question = (
        "what is" in question_normalized
        or "define" in question_normalized
        or "explain" in question_normalized
    )

    if conceptual_question:

        if "exercises" in page_text:
            score -= 15

        if "short answer questions" in page_text:
            score -= 8

        if "long answer questions" in page_text:
            score -= 8

    # ========================================================
    # 6. Strong penalty for clearly unrelated exercise pages
    # ========================================================

    if (
        "exercises" in page_text
        and not numerical_terms.intersection(question_words)
    ):
        score -= 10

    return score

# ============================================================
# RETRIEVE CONTEXT
# ============================================================

def retrieve_context(
    class_name,
    volume,
    unit_number,
    question,
    max_pages=5,
    max_context_chars=18000
):

    file_path = load_unit_file(
        class_name,
        volume,
        unit_number
    )

    if file_path is None:

        return {
            "source_file": None,
            "context": "",
            "chunks": [],
            "pages": []
        }

    text = file_path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    pages = split_into_pages(text)

    if not pages:

        return {
            "source_file": str(file_path),
            "context": "",
            "chunks": [],
            "pages": []
        }

    # ========================================================
    # SCORE EVERY PAGE
    # ========================================================

    scored_pages = []

    for index, page in enumerate(pages):

        score = score_page(
            page,
            question
        )

        scored_pages.append({
            "index": index,
            "score": score,
            "source_page": page["source_page"],
            "pdf_page": page["pdf_page"],
            "text": page["text"]
        })

    # ========================================================
    # FIND THE STRONGEST RELEVANT TEXTBOOK SECTION
    # ========================================================

    scored_pages.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # The strongest page becomes the primary anchor.
    # This prevents unrelated distant sections from
    # being selected just because they contain some
    # matching physics keywords.

    primary_anchor = None

    for page in scored_pages:

        if page["score"] > 0:
            primary_anchor = page
            break

    if primary_anchor is None:

        primary_anchor = scored_pages[0]


    # ========================================================
    # ADD ONLY LOCAL NEIGHBOURING PAGES
    # ========================================================

    selected_indices = set()

    anchor_index = primary_anchor["index"]

    # Textbook explanations often continue across
    # consecutive pages. Retrieve a local section
    # around the strongest page.
    for offset in [-2, -1, 0, 1, 2]:

        neighbour = anchor_index + offset

        if 0 <= neighbour < len(pages):

            selected_indices.add(neighbour)

    # ========================================================
    # BUILD CANDIDATE PAGES
    # ========================================================

    candidates = []

    for index in selected_indices:

        page = pages[index]

        score = score_page(
            page,
            question
        )

        candidates.append({
            "score": score,
            "source_page": page["source_page"],
            "pdf_page": page["pdf_page"],
            "text": page["text"]
        })

    # ========================================================
    # RANK CANDIDATES
    # ========================================================

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # ========================================================
    # LIMIT PAGE COUNT + CONTEXT SIZE
    # ========================================================

    selected = []

    total_chars = 0

    for page in candidates:

        page_block = (
            f"SOURCE_PAGE: {page['source_page']}\n"
            f"PDF_PAGE: {page['pdf_page']}\n\n"
            f"{page['text']}"
        )

        if (
            total_chars + len(page_block)
            > max_context_chars
        ):
            continue

        selected.append(page)

        total_chars += len(page_block)

        if len(selected) >= max_pages:
            break

    # ========================================================
    # RETURN IN TEXTBOOK ORDER
    # ========================================================

    selected.sort(
        key=lambda page: page["source_page"]
    )

    # ========================================================
    # BUILD FINAL CONTEXT
    # ========================================================

    context_parts = []

    for page in selected:

        context_parts.append(
            "\n".join([
                "------------------------------------------------------------",
                f"SOURCE_PAGE: {page['source_page']}",
                f"PDF_PAGE: {page['pdf_page']}",
                "------------------------------------------------------------",
                page["text"]
            ])
        )

    context = "\n\n".join(
        context_parts
    )

    return {
        "source_file": str(file_path),
        "context": context,
        "chunks": selected,
        "pages": [
            page["source_page"]
            for page in selected
        ]
    }