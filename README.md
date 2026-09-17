# Rivora AI

**Rivora AI** is a research-oriented prototype: an AI-powered community flood risk and preparedness assistant.

It is built as a **hybrid intelligence** system. A deterministic risk engine produces an immutable risk tier. IBM Granite is used only to explain that fixed result and to generate preparedness narrative. Retrieval-augmented generation (RAG) grounds knowledge-based answers in a curated knowledge base. Granite must never override or reclassify the engine’s tier.

Primary SDG: **SDG 11** (Sustainable Cities and Communities). Secondary: SDG 13, SDG 6.

This repository is an internship prototype (IBM SkillsBuild + AICTE context). It is **not** a beginner toy demo, and it is **not** an operational flood-warning service.

## Setup

1. Install **Python 3.11 or newer**.
2. From the project root (`RIVORA-AI`):

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set:

- `WATSONX_API_KEY`
- `WATSONX_PROJECT_ID`
- `WATSONX_URL`
- `GRANITE_MODEL_ID`

Embeddings run locally via `sentence-transformers`; they do not use these keys. Live Granite calls require a configured watsonx.ai project. The engine, catalogue, and most tests are designed to run without the LLM.

4. Do not commit `.env`. Vector-store files under `vector_store/` are generated later and are git-ignored.

## Run

After Sub-Task 8 (Streamlit UI) is implemented:

```bash
streamlit run app/main.py
```

The application is **not runnable as a product** at Sub-Task 1. Scaffolding only creates the directory layout and environment files.

Tests (after later sub-tasks add them):

```bash
pytest
```

Do not treat empty or pending tests as accuracy results. Report test numbers only after tests have actually been run.

## Responsible AI notice

Rivora AI:

- does **not** issue official flood warnings;
- does **not** provide exact flood predictions or hydrological forecasts;
- does **not** authorize validated real-world emergency decisions.

Official guidance and warnings remain the responsibility of authorities such as India’s National Disaster Management Authority (NDMA), State Disaster Management Authorities, the India Meteorological Department (IMD), and local emergency services.

User-reported inputs are not sensor or satellite observations. The scoring model is a structured approximation, not a validated hydrological model. RAG answers must be grounded in retrieved sources; if evidence is insufficient, the system must say so rather than invent content. Evidence catalogue entries must be real and verifiable. Accuracy percentages and real-world impact figures must not be fabricated.

## Project layout

See `rivora-ai-plan.md` for the approved architecture and sub-task sequence.

## License / status

Prototype under active implementation. Implementation proceeds one sub-task at a time per the approved plan.
