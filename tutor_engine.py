from app_config import get_sarvam_api_key
import os

from sarvamai import SarvamAI

from retriever import retrieve_context


# =========================================================
# SARVAM CLIENT
# =========================================================

def get_client():

    api_key = get_sarvam_api_key()

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not set. "
            "Please configure it in PowerShell."
        )

    return SarvamAI(
        api_subscription_key=api_key
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Physics Mentor AI, a careful Tamil Nadu State Board
XI and XII Physics tutor.

Your job is to teach Physics clearly and accurately using the
supplied official Tamil Nadu State Board Physics textbook context.

IMPORTANT GROUNDING RULES:

1. Use the supplied textbook context as the primary source of truth.

2. Do not invent textbook page numbers.

3. Do not claim that something appears in the textbook unless
   it is supported by the supplied context.

4. If the supplied textbook context is insufficient, clearly say:
   "The available textbook context is insufficient to answer this reliably."

5. Explain Physics in simple language suitable for XI/XII students.

6. Preserve correct Physics terminology, equations and SI units.

7. Do not introduce unrelated textbook topics.

8. Distinguish textbook-supported information from simple explanations
   or analogies.

9. Give a complete, student-facing explanation at the depth the question needs. Do not reduce a multi-step derivation or numerical problem to a few lines.
10. For a derivation or long-answer question, explain the physical principle, assumptions, each algebraic step, and the final result. Do not skip intermediate steps.
11. For a numerical problem, show Given, Find, Formula, unit conversion if needed, Substitution, each calculation step, SI unit, final answer, and a brief reasonableness check. Preserve signs and significant figures where relevant.
12. For a conceptual question, explain what the concept means, why it works, the relevant equation and symbols, a textbook-supported example, common misconception, and exam tip.
13. Match the depth to the student's request and likely exam marks. If the student asks for a detailed explanation, provide one.

FOR NUMERICAL QUESTIONS:

Given:
Find:
Formula:
Substitution:
Calculation:
Unit:
Final Answer:
Common Mistake:

FOR CONCEPTUAL QUESTIONS:

Concept:
Simple Explanation:
Formula:
Example:
Common Mistake:
Exam Tip:

Always finish with the textbook source.
"""


# =========================================================
# PHYSICS TUTOR
# =========================================================

def ask_physics_tutor(
    class_name,
    volume,
    unit_number,
    question,
    language="English"
):

    # -----------------------------------------------------
    # RETRIEVE RELEVANT TEXTBOOK PAGES
    # -----------------------------------------------------

    result = retrieve_context(
        class_name=class_name,
        volume=volume,
        unit_number=unit_number,
        question=question,
        max_pages=5,
        max_context_chars=12000
    )

    context = result["context"]

    if not context:

        return {
            "answer": (
                "The available textbook context is insufficient "
                "to answer this reliably."
            ),
            "pages": [],
            "source_file": result["source_file"]
        }

    # -----------------------------------------------------
    # LANGUAGE INSTRUCTION
    # -----------------------------------------------------

    if language == "Tamil":

        language_instruction = """
Answer completely in Tamil.

Keep Physics equations, symbols and SI units accurate.

Use standard Tamil Physics terminology where appropriate.
Where useful, include the English Physics term in brackets.

Do not translate equations.
"""

    elif language == "English + Tamil":

        language_instruction = """
First explain the answer in simple English.

Then provide the corresponding Tamil explanation.

Keep equations, Physics symbols and SI units unchanged.
"""

    else:

        language_instruction = """
Answer in simple, clear English suitable for an XI/XII
Tamil Nadu State Board Physics student.
"""

    # -----------------------------------------------------
    # USER PROMPT
    # -----------------------------------------------------

    user_prompt = f"""
Student question:

{question}

Student class:
{class_name}

Textbook volume:
{volume}

Textbook unit:
Unit {unit_number}

Language:
{language}

{language_instruction}

IMPORTANT:

Answer the student's question using the supplied official
textbook context below.

Relevant textbook context:

{context}

Use only the relevant information needed to answer the question.

At the end, provide:

Source:
Tamil Nadu State Board Physics textbook
Textbook page(s): {result["pages"]}
"""

    # -----------------------------------------------------
    # CALL SARVAM
    # -----------------------------------------------------

    client = get_client()

    response = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2,
        max_tokens=2200,
        reasoning_effort=None
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "pages": result["pages"],
        "source_file": result["source_file"]
    }