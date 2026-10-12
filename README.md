# Physics Mentor AI — AI Avatar Physics Tutor

An AI-assisted Physics learning application for Tamil Nadu State Board Classes XI and XII. It combines textbook-oriented retrieval, previous-year question practice, explanations, adaptive quizzes, learning insights, diagram discovery, and optional Tamil/English voice interaction in a Streamlit interface.

> **Project status:** Local development and release validation in progress. Some question records and diagram metadata still require verification. Deployment should be treated as a preview until those checks and a full application smoke test are complete.

## Objective

Help students revise Physics concepts, practise examination-style questions, understand solutions, and identify topics that need more attention through a single learning interface.

## Key Features

- **Chapter-based tutoring:** Retrieve relevant textbook-oriented content across 22 Class XI and XII units.
- **Previous-year questions (PYQs):** Browse and practise a curated question dataset, with answer and explanation workflows.
- **Adaptive quizzes:** Practise multiple-choice questions and use quiz results to guide revision.
- **Learning insights:** Review topic performance, recent attempts, and areas for improvement.
- **Diagram discovery:** Search an indexed collection of textbook-page diagram candidates.
- **Bilingual and voice workflows:** English/Tamil support and optional Sarvam-powered voice features, depending on configuration and API availability.
- **Progress tracking:** Local progress storage for development; hosted deployments must use isolated session storage unless a separate persistent, user-isolated storage system is implemented.
- **Streamlit interface:** A Python application designed for interactive learning and rapid iteration.

## Typical Student Workflow

1. Select a class and Physics unit.
2. Ask a concept question and review the retrieved learning context.
3. Practise a previous-year question or take a quiz.
4. Read the answer or explanation and revisit weak topics.
5. Use diagram search or optional voice interaction where available.

## Technology Stack

- Python
- Streamlit
- Pandas and NumPy
- Sarvam AI SDK for configured language and voice workflows
- JSON-based question, mapping, textbook-index, and diagram-index assets
- Python modules for retrieval, tutoring, quizzes, PYQ workflows, mastery tracking, and learning insights

## Repository Structure

```text
AI-Avatar-Physics-Tutor/
├── app.py
├── app_config.py
├── tutor_engine.py
├── retriever.py
├── quiz_engine.py
├── voice_engine.py
├── pyq_ui.py
├── pyq_answer_engine.py
├── pyq_explanation_engine.py
├── pyq_mastery_engine.py
├── progress_engine.py
├── weak_topic_engine.py
├── textbook_diagram_engine.py
├── session_manager.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── class11/
│   ├── class12/
│   ├── textbook_unit_index.json
│   ├── pyq_questions/
│   ├── pyq_pages/
│   └── textbook_diagrams/
└── textbooks/   # Source PDFs; include only if required and redistribution is permitted

Additional development and verification scripts may exist locally and are not necessarily part of the public release.

Local Setup

1. Requirements

Python 3.12 recommended

Git

A virtual environment

A Sarvam API key only for features that call Sarvam services

2. Create and activate a virtual environment

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

3. Configure secrets

For hosted deployment, add secrets through the hosting platform's secret-management interface. Do not commit .env or .streamlit/secrets.toml.

Example Streamlit secrets configuration:

SARVAM_API_KEY = "YOUR_API_KEY"
PROGRESS_MODE = "session"

Replace the placeholder locally in the hosting platform's secret editor; never publish a real key in this README or in source control.

PROGRESS_MODE = "session" selects session-scoped progress where supported by the application. Session state is temporary and is not a persistent student account or database.

For local development, app_config.py reads environment variables and then Streamlit secrets. The project does not currently demonstrate automatic .env loading in its main configuration path, so configure local environment variables explicitly unless .env loading is added and tested.

4. Start the application

python -m streamlit run app.py

Open the local URL printed by Streamlit.

Configuration

Setting

Purpose

SARVAM_API_KEY

Enables configured Sarvam-powered features

PROGRESS_MODE

Selects session-scoped progress when set to session, session_state, or temporary

Keep credentials private. Do not paste keys into issue reports, logs, screenshots, README files, or Git commits.

Validation

The development workflow includes Python compilation checks, local/offline checks, retrieval checks, and question-data review scripts.

Validation already performed during development includes Python module compilation and offline configuration/data checks. These checks do not, by themselves, prove that every UI workflow works end-to-end or that every answer is correct.

Before public release:

Run the application locally and check the main pages and navigation.

Test tutoring, quizzes, PYQ answers and explanations, progress, diagrams, and language/voice options.

Verify question options and answer keys against original papers.

Review diagram labels and source-page references.

Confirm that secrets, local progress, caches, backups, and temporary audit files are excluded from Git.

Confirm that hosted users cannot read or overwrite another user's progress.

Confirm that required assets are present in the deployed repository.

Check that the application starts successfully on the hosting platform.

Data Quality and Limitations

The development dataset contains 494 PYQ records and 195 MCQs. These counts describe the current dataset, not a claim that every item has been fully verified.

Some MCQ options/answers still need comparison with the original question papers. The diagram index also contains candidates whose labels or page mappings require review. Treat generated explanations as study assistance and verify important examination answers against the prescribed textbook and official materials.

AI-generated responses may be incomplete or incorrect. Voice features depend on API availability, valid configuration, and applicable service limits.

Privacy and Deployment

Local progress and mastery files are development data and must not be committed.

Do not use a shared writable JSON file as public multi-user storage.

Session state provides temporary session isolation, not durable account-based progress.

Never include API keys or private credentials in Git.

Include textbook PDFs or other source materials in a public repository only when their licence and redistribution terms allow it.

Keep the public deployment in preview until the validation checklist is complete.

Roadmap

Complete end-to-end regression testing.

Verify remaining PYQ answer keys and diagram metadata.

Improve retrieval relevance and the quality of source references.

Review hosted session isolation and operational error handling.

Deploy a public preview and document known limitations.

Author

Developed as an AI-assisted Physics learning project combining Python application development, retrieval, data processing, question practice, and educational workflows.
