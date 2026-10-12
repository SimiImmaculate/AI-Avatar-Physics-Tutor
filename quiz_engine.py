import json
import os
import re
import math
import ast
import operator

from sarvamai import SarvamAI

from retriever import retrieve_context


# =========================================================
# SARVAM CLIENT
# =========================================================

def get_client():
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not set. "
            "Please configure it in PowerShell."
        )

    return SarvamAI(
        api_subscription_key=api_key
    )


# =========================================================
# SAFE MATH EVALUATION
# =========================================================

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    """
    Safely evaluate a simple numerical expression.

    Examples:
        20**2 / (2*10)
        0 + 2*5
        400 / 20

    Returns:
        float or None
    """

    try:
        node = ast.parse(
            expression,
            mode="eval"
        ).body

        def evaluate(current):

            if isinstance(current, ast.Constant):
                if isinstance(current.value, (int, float)):
                    return current.value

                raise ValueError(
                    "Unsupported constant"
                )

            if isinstance(current, ast.BinOp):
                operation = _ALLOWED_OPERATORS.get(
                    type(current.op)
                )

                if operation is None:
                    raise ValueError(
                        "Unsupported operator"
                    )

                left = evaluate(current.left)
                right = evaluate(current.right)

                return operation(
                    left,
                    right
                )

            if isinstance(current, ast.UnaryOp):
                operation = _ALLOWED_OPERATORS.get(
                    type(current.op)
                )

                if operation is None:
                    raise ValueError(
                        "Unsupported unary operator"
                    )

                return operation(
                    evaluate(current.operand)
                )

            raise ValueError(
                "Unsupported expression"
            )

        result = evaluate(node)

        if not math.isfinite(result):
            return None

        return float(result)

    except Exception:
        return None


# =========================================================
# NUMERICAL VALIDATION
# =========================================================

def validate_numerical_question(question):
    """
    Validate the numerical solution supplied by the AI.

    The AI must provide:
        verification_expression
        expected_numeric_answer

    Python independently evaluates the expression and checks
    whether it matches the expected numerical answer.

    This prevents obvious calculation inconsistencies.
    """

    if question.get("type") != "numerical":
        return True

    expression = question.get(
        "verification_expression"
    )

    expected = question.get(
        "expected_numeric_answer"
    )

    if expression is None or expected is None:
        return False

    calculated = safe_calculate(
        str(expression)
    )

    if calculated is None:
        return False

    try:
        expected = float(expected)
    except (TypeError, ValueError):
        return False

    if not math.isclose(
        calculated,
        expected,
        rel_tol=1e-6,
        abs_tol=1e-6
    ):
        return False

    # The independently calculated result must also agree with the
    # option marked as correct. Otherwise a mathematically valid
    # expression could coexist with a wrong correct_option index.
    options = question.get("options", [])
    correct_index = question.get("correct_option")
    if not isinstance(options, list) or len(options) != 4:
        return False
    if not isinstance(correct_index, int) or correct_index not in range(4):
        return False

    parsed_options = []
    for option in options:
        option_text = str(option).replace("−", "-")
        match = re.search(
            r"[-+]?\s*(?:\d+(?:,\d{3})*(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
            option_text
        )
        if not match:
            return False
        token = match.group(0).replace(",", "").strip()
        try:
            value = float(token)
        except ValueError:
            return False
        # Permit ordinary rounding in displayed MCQ choices (e.g. 6.32
        # for 6.3249), but do not silently convert units.
        decimals = len(token.split(".", 1)[1].split("e", 1)[0]) if "." in token else 0
        tolerance = max(1e-6, 0.5 * (10 ** (-decimals)))
        parsed_options.append((value, tolerance))

    correct_value, correct_tolerance = parsed_options[correct_index]
    if abs(correct_value - expected) > correct_tolerance + 1e-12:
        return False

    # Reject ambiguous choices that both round to the calculated answer.
    matches = sum(
        abs(value - expected) <= tolerance + 1e-12
        for value, tolerance in parsed_options
    )
    return matches == 1


# =========================================================
# BASIC QUESTION VALIDATION
# =========================================================

def validate_question_structure(question):

    required_fields = [
        "id",
        "difficulty",
        "type",
        "question",
        "options",
        "correct_option",
        "explanation",
        "source_pages"
    ]

    if not all(
        field in question
        for field in required_fields
    ):
        return False

    if not isinstance(
        question["options"],
        list
    ):
        return False

    if len(question["options"]) != 4:
        return False

    if any(not str(option).strip() for option in question["options"]):
        return False

    if len({str(option).strip().casefold() for option in question["options"]}) != 4:
        return False

    if not str(question.get("question", "")).strip():
        return False

    if not str(question.get("explanation", "")).strip():
        return False

    if question["difficulty"] not in [
        "easy",
        "medium",
        "hard"
    ]:
        return False

    if question["type"] not in [
        "conceptual",
        "numerical",
        "formula",
        "mcq"
    ]:
        return False

    if not isinstance(
        question["correct_option"],
        int
    ):
        return False

    if question["correct_option"] not in [
        0,
        1,
        2,
        3
    ]:
        return False

    if not isinstance(
        question["source_pages"],
        list
    ):
        return False

    return True


# =========================================================
# GENERATE ADAPTIVE QUIZ BANK
# =========================================================

def generate_quiz_bank(
    class_name,
    volume,
    unit_number,
    number_per_level=3
):
    """
    Generate a textbook-grounded adaptive quiz bank.

    Creates:
        Easy
        Medium
        Hard

    Questions are validated before entering the quiz.
    """

    result = retrieve_context(
        class_name=class_name,
        volume=volume,
        unit_number=unit_number,
        question=(
            "Important concepts, formulas, definitions, "
            "examples and numerical problems from this unit"
        ),
        max_pages=10,
        max_context_chars=18000
    )

    context = result["context"]

    if not context:
        raise RuntimeError(
            "The available textbook context is insufficient "
            "to generate a reliable quiz."
        )

    system_prompt = """
You are Physics Mentor AI, an expert Tamil Nadu State Board
XI and XII Physics quiz creator.

Create a reliable, textbook-grounded Physics quiz.

STRICT RULES:

1. Use ONLY the supplied textbook context.
2. Do not invent textbook facts.
3. Do not use knowledge outside the supplied context.
4. Every question must have exactly four options.
5. Exactly one option must be correct.
6. Questions must be suitable for the selected class and unit.
7. Include:
   - conceptual questions
   - formula-based questions
   - numerical questions
8. Numerical questions must be unambiguous.
9. Avoid duplicate questions.
10. Avoid questions requiring unavailable diagrams.
11. Do not include the answer inside the question.
12. Keep questions concise and exam-oriented, but make the explanation educational and sufficiently detailed.
13. For numerical explanations, show Given, Find, Formula, unit conversion when needed, Substitution, step-by-step Calculation, Final Answer with unit, and Common Mistake.
14. For conceptual/formula explanations, explain the principle, define symbols, show relevant equation and reasoning, and finish with an Exam Tip.
15. The correct answer must be represented by:
    0, 1, 2 or 3.
14. For numerical questions, provide a verification
    expression that Python can calculate independently.
15. The verification expression must contain ONLY numbers
    and arithmetic operators.
16. The expected_numeric_answer must be the numerical value
    obtained from that expression.
17. Never invent a numerical answer.
18. Check your numerical calculation before returning JSON.

For numerical questions use:

"verification_expression": "400/(2*10)",
"expected_numeric_answer": 20

Return ONLY valid JSON.

Required JSON structure:

{
  "questions": [
    {
      "id": "easy_1",
      "difficulty": "easy",
      "type": "conceptual",
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correct_option": 0,
      "explanation": "Short explanation",
      "source_pages": [73]
    },
    {
      "id": "medium_1",
      "difficulty": "medium",
      "type": "numerical",
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correct_option": 1,
      "explanation": "Short explanation",
      "source_pages": [76, 77],
      "verification_expression": "400/(2*10)",
      "expected_numeric_answer": 20
    }
  ]
}
"""

    user_prompt = f"""
Class:
{class_name}

Volume:
{volume}

Unit:
Unit {unit_number}

Generate exactly {number_per_level} easy,
{number_per_level} medium and
{number_per_level} hard questions.

Therefore generate exactly:
{number_per_level * 3} questions total.

Textbook context:

{context}
"""

    client = get_client()

    response = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.1,
        max_tokens=6000,
        reasoning_effort=None
    )

    raw = response.choices[0].message.content.strip()

    # -----------------------------------------------------
    # CLEAN MARKDOWN FENCES
    # -----------------------------------------------------

    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw
    )

    # -----------------------------------------------------
    # PARSE JSON
    # -----------------------------------------------------

    try:
        quiz_data = json.loads(raw)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Quiz generation returned invalid JSON: {e}"
        )

    questions = quiz_data.get(
        "questions",
        []
    )

    if not questions:
        raise RuntimeError(
            "No quiz questions were generated."
        )

    # -----------------------------------------------------
    # VALIDATE QUESTIONS
    # -----------------------------------------------------

    validated = []

    seen_questions = set()

    for question in questions:

        if not validate_question_structure(
            question
        ):
            continue

        question_text = (
            question["question"]
            .strip()
            .lower()
        )

        # Prevent duplicates
        if question_text in seen_questions:
            continue

        seen_questions.add(
            question_text
        )

        # Numerical validation
        if question["type"] == "numerical":

            if not validate_numerical_question(
                question
            ):
                continue

        validated.append(
            question
        )

    # -----------------------------------------------------
    # REQUIRE SUFFICIENT QUESTIONS
    # -----------------------------------------------------

    if len(validated) < 6:

        raise RuntimeError(
            "The quiz generator did not produce enough "
            "validated questions. Please generate the quiz again."
        )

    return {
        "questions": validated,
        "source_pages": result["pages"],
        "source_file": result["source_file"]
    }


# =========================================================
# ADAPTIVE QUESTION SELECTION
# =========================================================

def choose_next_question(
    questions,
    used_ids,
    difficulty
):
    """
    Select an unused question at the requested difficulty.
    """

    available = [
        q
        for q in questions
        if q["id"] not in used_ids
    ]

    if not available:
        return None

    exact = [
        q
        for q in available
        if q["difficulty"] == difficulty
    ]

    if exact:
        return exact[0]

    difficulty_order = {
        "easy": 0,
        "medium": 1,
        "hard": 2
    }

    target = difficulty_order[
        difficulty
    ]

    available.sort(
        key=lambda q:
        abs(
            difficulty_order[
                q["difficulty"]
            ] - target
        )
    )

    return available[0]


# =========================================================
# ADAPTIVE DIFFICULTY
# =========================================================

def get_next_difficulty(
    current_difficulty,
    correct
):
    """
    Correct:
        increase difficulty

    Wrong:
        decrease difficulty
    """

    levels = [
        "easy",
        "medium",
        "hard"
    ]

    current_index = levels.index(
        current_difficulty
    )

    if correct:

        current_index = min(
            current_index + 1,
            len(levels) - 1
        )

    else:

        current_index = max(
            current_index - 1,
            0
        )

    return levels[current_index]