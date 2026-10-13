# Physics Mentor AI — AI Avatar Physics Tutor

**An AI-powered Physics learning platform for Tamil Nadu State Board Classes XI and XII, built with Python, Streamlit, and Sarvam AI.**

Physics Mentor AI brings together AI-assisted tutoring, textbook-oriented retrieval, previous-year question practice, adaptive quizzes, learning insights, textbook-page image discovery, and optional Tamil/English voice interaction in a single interactive application.

**Live Application:** [Physics Mentor AI](https://physics-mentor-ai.streamlit.app/)

## Overview

Physics Mentor AI is designed to make Physics learning more interactive, accessible, and effective for higher-secondary students. It combines structured educational resources with AI-powered explanations and practice workflows to help students understand concepts, prepare for examinations, and identify topics that need additional revision.

Powered by Sarvam AI for configured language and voice workflows, the application brings modern AI capabilities into a curriculum-oriented learning experience.

## Key Features

- **AI Physics Tutor:** Ask Physics questions and receive AI-assisted explanations supported by textbook-oriented retrieval.
- **Class XI and XII Learning:** Access educational content organized across 22 Physics units.
- **Previous-Year Questions (PYQs):** Browse and practise a curated collection of examination-oriented questions.
- **Interactive MCQ Quizzes:** Practise multiple-choice questions and receive feedback to support revision.
- **Answer Explanations:** Explore solutions and explanations for supported question workflows.
- **Learning Insights:** Review learning performance, topic mastery, recent attempts, and areas for improvement.
- **Textbook Image Discovery:** Search an indexed collection of textbook-page images to explore relevant figures and educational context.
- **Tamil and English Support:** Use configured bilingual language workflows.
- **AI Voice Capabilities:** Access optional Sarvam-powered speech and language features when configured and available.
- **Session-Based Progress:** Support temporary progress tracking within the configured application session.
- **Interactive Web Interface:** Access learning features through a Streamlit application deployed on Streamlit Community Cloud.

## Live Demo

**Try the application:** https://physics-mentor-ai.streamlit.app/

The deployed application has been tested across its main learning workflows, including tutoring, quizzes, previous-year question browsing, progress behaviour, and textbook image rendering.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and data processing |
| Streamlit | Interactive web interface |
| Sarvam AI SDK and APIs | Configured AI language and voice workflows |
| Pandas | Structured data processing |
| NumPy | Numerical operations |
| JSON | Educational datasets, indexes, and metadata |
| Git and GitHub | Version control and source-code management |
| Streamlit Community Cloud | Application hosting and deployment |

## Application Architecture

The application uses modular Python components to organize its main learning workflows.

- **Tutor and Retrieval Layer:** Retrieves relevant educational context and supports AI-assisted tutoring.
- **Quiz Layer:** Manages multiple-choice practice and quiz interactions.
- **PYQ Layer:** Supports question browsing, answers, explanations, and related learning workflows.
- **Progress and Insights Layer:** Organizes session progress, mastery information, and weak-topic insights.
- **Textbook Diagram Layer:** Searches diagram metadata and resolves the corresponding rendered textbook-page images.
- **Voice Layer:** Integrates configured Sarvam-powered voice capabilities.
- **Application Layer:** Connects the modules through a Streamlit interface.

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
└── textbooks/
```

The repository contains the application code, educational datasets, retrieval resources, question metadata, and textbook diagram indexes required by the implemented workflows. Source PDFs are subject to applicable licensing and redistribution permissions.

## Getting Started

### Prerequisites

- Python 3.12 recommended
- Git
- A Sarvam AI API key for features that require Sarvam services

### 1. Clone the repository

```bash
git clone https://github.com/SimiImmaculate/AI-Avatar-Physics-Tutor.git
cd AI-Avatar-Physics-Tutor
```

Repository authentication is required if the GitHub repository is private.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure application secrets

Configure credentials using environment variables or Streamlit's secrets mechanism.

For Streamlit secrets, the configuration format is:

```toml
SARVAM_API_KEY = "YOUR_API_KEY"
PROGRESS_MODE = "session"
```

Replace the placeholder with your own API key in your local configuration. For hosted deployments, configure secrets through the hosting platform's secret-management interface.

**Never commit real API keys, passwords, or private credentials to GitHub.**

The application configuration reads environment variables and then Streamlit secrets. Configure local environment variables explicitly unless automatic `.env` loading has been implemented.

Session-based progress is temporary and should not be treated as persistent account-based storage.

### 4. Run the application

```powershell
python -m streamlit run app.py
```

Open the local URL provided by Streamlit.

## AI Integration with Sarvam

Sarvam AI provides the language and speech capabilities used by the application's configured AI workflows.

Depending on configuration and service availability, the integration supports:

- AI-assisted educational conversations
- Tamil and English language workflows
- Speech-related functionality
- Voice-enabled learning interactions

The application uses a configurable API-based integration, allowing the relevant AI functionality to be managed through application settings and securely configured credentials.

Actual feature availability depends on the configured models, API access, network connectivity, and service limits.

## Validation and Reliability

The deployed application has been smoke-tested, and the principal learning workflows have been exercised successfully.

Validation includes:

- Application startup and hosted deployment
- AI Physics tutoring interactions
- MCQ quiz interaction and feedback
- Previous-year question browsing
- Session-based progress behaviour
- Textbook-page image rendering

The textbook image resolution issue was corrected by normalizing stored image paths before resolving them. The corrected version was committed to GitHub and deployed successfully.

Question-answer correctness and diagram-caption accuracy remain separate educational quality considerations. Students should verify important examination answers against prescribed textbooks and official educational materials.

## Privacy, Security, and Data Handling

- API keys are configured through environment variables or the hosting platform's secrets management.
- Private credentials must never be included in source control.
- Local progress files, backups, and temporary verification artifacts should remain excluded from the deployed application where appropriate.
- Session state provides temporary session isolation, not durable student accounts.
- Public multi-user deployments should not rely on a shared writable JSON file for private student records.
- Textbook PDFs and other third-party resources must comply with their applicable licensing and redistribution terms.

## Future Enhancements

- Improve retrieval relevance and educational source references.
- Expand verified examination-question coverage.
- Refine diagram-caption and source-page mapping.
- Enhance bilingual tutoring and voice interaction.
- Introduce secure persistent student profiles and long-term learning analytics.
- Extend automated testing and educational content validation.

## Author

**Simi Immaculate**

M.Sc. Mathematics | Data Science & Machine Learning
