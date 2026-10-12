from app_config import get_sarvam_api_key
import os
import json
from pathlib import Path
from datetime import datetime

from sarvamai import SarvamAI

from pyq_answer_engine import answer_pyq


BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = BASE_DIR / "data" / "pyq_answers"
CACHE_FILE = CACHE_DIR / "pyq_explanation_cache.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SARVAM CLIENT
# ============================================================

def get_client():
    api_key = get_sarvam_api_key()

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not available in the environment."
        )

    return SarvamAI(
        api_subscription_key=api_key
    )


# ============================================================
# CACHE
# ============================================================

def load_cache():

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception:
        return {}


def save_cache(cache):

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# LANGUAGE INSTRUCTIONS
# ============================================================

def language_instruction(language):

    if language == "Tamil":
        return """
Write the explanation completely in Tamil.

Keep Physics terms, mathematical symbols, formulas,
SI units and variable names unchanged.

Where useful, write the English Physics term in brackets
after the Tamil term.
"""

    if language == "English + Tamil":
        return """
First provide a clear English explanation.
Then provide the same explanation in Tamil.

Keep formulas, symbols and SI units unchanged.
"""

    return """
Write the explanation in simple, clear English suitable
for Tamil Nadu State Board XI/XII students.
"""


# ============================================================
# GENERATE INTELLIGENT EXPLANATION
# ============================================================

def generate_explanation(
    class_name,
    year,
    question_number,
    language="English"
):

    cache = load_cache()

    # Version the key so older short explanations do not override the
    # improved detailed explanation prompt.
    cache_key = (
        f"v2_{class_name}_{year}_Q{question_number}_{language}"
    )

    if cache_key in cache:

        result = cache[cache_key]
        result["from_cache"] = True

        return result

    # --------------------------------------------------------
    # Get the existing textbook-grounded answer
    # --------------------------------------------------------

    answer_result = answer_pyq(
        class_name=class_name,
        year=year,
        question_number=question_number,
        language=language
    )

    if not answer_result.get("success"):

        return {
            "success": False,
            "error": answer_result.get(
                "error",
                "Unable to generate PYQ answer."
            )
        }

    question = answer_result.get(
        "question",
        ""
    )

    answer = answer_result.get(
        "answer",
        ""
    )

    unit = answer_result.get(
        "unit",
        ""
    )

    unit_title = answer_result.get(
        "unit_title",
        ""
    )

    topic = answer_result.get(
        "topic",
        ""
    )

    pages = answer_result.get(
        "pages",
        []
    )

    confidence = answer_result.get(
        "confidence",
        0
    )

    # --------------------------------------------------------
    # SECTION INSTRUCTIONS
    # --------------------------------------------------------

    if language == "English":

        section_instruction = """
Write ONLY in English.

Use these exact headings:

CONCEPT:
GIVEN:
FORMULA:
SOLUTION:
FINAL ANSWER:
COMMON MISTAKE:
EXAM TIP:

Do not use Tamil headings.
Do not output instructions to yourself.
Do not write phrases such as "First explain..." or
"Then provide...".
"""

    elif language == "Tamil":

        section_instruction = """
Write ONLY in Tamil.

Use these exact headings:

கருத்து:
கொடுக்கப்பட்டவை:
சூத்திரம்:
தீர்வு:
இறுதி விடை:
பொதுவான தவறு:
தேர்வு குறிப்பு:

Do not use English section headings.
Do not output instructions to yourself.
Do not write phrases such as "First explain..." or
"Then provide...".
"""

    else:

        section_instruction = """
Give the explanation in two parts.

PART 1 — ENGLISH

Use these exact English headings:

CONCEPT:
GIVEN:
FORMULA:
SOLUTION:
FINAL ANSWER:
COMMON MISTAKE:
EXAM TIP:

PART 2 — TAMIL

Use these exact Tamil headings:

கருத்து:
கொடுக்கப்பட்டவை:
சூத்திரம்:
தீர்வு:
இறுதி விடை:
பொதுவான தவறு:
தேர்வு குறிப்பு:

Do not output meta-instructions.
Do not write "First explain..." or "Then provide...".
Only provide the actual Physics explanation.
"""

    # --------------------------------------------------------
    # AI EXPLANATION PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are the final explanation layer of a Tamil Nadu State Board
Physics examination tutor.

The answer below has already been generated using the official
Tamil Nadu State Board Physics textbook context.

Do NOT contradict the supplied answer.
Do NOT invent textbook facts.
Do NOT invent page numbers.
Do NOT introduce unrelated concepts.

Question:
{question}

Textbook Unit:
{unit} — {unit_title}

Topic:
{topic}

Textbook Pages:
{pages}

Textbook-grounded Answer:
{answer}

{language_instruction(language)}

{section_instruction}

Use standard LaTeX for equations.

Use:
$...$ for inline equations
$$...$$ for display equations

Do NOT use:
\\(...\\)
\\[...\\]

Give a complete, exam-ready explanation proportional to the question's marks.
For numerical questions, show every substitution and arithmetic step, unit conversions, sign conventions when relevant, the final answer with unit, and a quick check of the result.
For derivations, explain the principle, assumptions and each algebraic step; do not skip steps.
For conceptual questions, explain the meaning, reasoning, symbols, and a relevant textbook-supported example.
Include a useful common mistake and exam tip. Do not pad the answer with unrelated information.
Finish every section.
"""

    # --------------------------------------------------------
    # CALL SARVAM
    # --------------------------------------------------------

    client = get_client()

    response = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise Tamil Nadu State Board "
                    "XI/XII Physics tutor. "
                    "Use only the supplied textbook-grounded "
                    "answer and context."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=3000,
        reasoning_effort=None
    )

    explanation = response.choices[0].message.content

    # --------------------------------------------------------
    # BUILD RESULT
    # --------------------------------------------------------

    result = {
        "success": True,
        "class": class_name,
        "year": year,
        "question_number": question_number,
        "question": question,
        "unit": unit,
        "unit_title": unit_title,
        "topic": topic,
        "textbook_pages": pages,
        "confidence": confidence,
        "base_answer": answer,
        "explanation": explanation,
        "language": language,
        "generated_at": datetime.now().isoformat(),
        "from_cache": False
    }

    # --------------------------------------------------------
    # SAVE TO CACHE
    # --------------------------------------------------------

    cache[cache_key] = result

    save_cache(cache)

    return result