# Rivora AI — Implementation Plan

## Status Key
- `[ ]` pending
- `[-]` in progress
- `[x]` done

---

## Top-Level Overview

**Goal:** Build a technically strong, professionally presentable, **research-oriented prototype** (not a beginner/demo toy) for the IBM SkillsBuild + AICTE internship context (1M1B AI for Sustainability programme where that affiliation is real and relevant). The product name is **Rivora AI**.

**System Name:** Rivora AI: AI-Powered Community Flood Risk and Preparedness Assistant

**Primary SDG:** SDG 11 — Sustainable Cities and Communities
**Secondary SDGs:** SDG 13 — Climate Action, SDG 6 — Clean Water and Sanitation

**Core Design Principle:**
A hybrid intelligence system where a transparent, deterministic risk-scoring engine produces an immutable risk tier (LOW / MODERATE / HIGH / VERY HIGH / INSUFFICIENT DATA), and IBM Granite LLM is used *only* for explanation generation and preparedness narrative — never for reclassifying risk. RAG grounds the LLM in an authoritative curated knowledge base. The system is modular, fully documented, and structured for future real-world expansion.

**Confirmed Technology Stack:**
- **Backend:** Python 3.11+
- **Frontend:** Streamlit
- **LLM:** IBM Granite via `langchain-ibm` (WatsonxLLM)
- **RAG orchestration:** LangChain
- **Vector store:** ChromaDB (local, file-based)
- **Knowledge base format:** Markdown files (curated content) + JSON catalogue (evidence/sources)
- **Embeddings:** `sentence-transformers` (local, no external API dependency for embeddings)

**Stack freeze:** Keep Python + Streamlit + LangChain + IBM Granite / WatsonxLLM + ChromaDB + `sentence-transformers` unless a **strong technical blocker** is documented (library incompatibility, model ID deprecation, or an irreplaceable API change). Preference changes or “nicer UI libraries” are not sufficient reasons to change the stack.

---

## Non-Negotiable Architectural Requirements

These requirements override any later convenience shortcut during implementation.

### Evidence integrity (no fabrication)
- Wherever the system makes **external claims** (facts, statistics, guidance attributed to an organization, news, research findings, URLs), those claims must rest on **real, verifiable sources**.
- **Do not invent or fabricate** sources, URLs, statistics, research findings, news articles, organizational names, affiliations, dates, or “impact” numbers.
- Knowledge-base Markdown must stay within general, citable flood/preparedness guidance. If a specific figure or named study is used, it must be backed by an evidence-catalogue entry with a real URL.
- If a fact cannot be sourced, **omit it** rather than paraphrasing a fake citation.

### Evidence / Sources layer (authority-aware)
The Evidence/Sources UI is a **curated catalogue**, not LLM-generated content. It must:
- Support credible source classes: **government / disaster-management**, **UN / intergovernmental**, **peer-reviewed research**, **reputable organizational**, and **news**.
- **Distinguish source type and authority** in the data model and in the UI (badges + short authority note), so evaluators can see that an NDMA guideline is not equivalent to a news recap or a social post.
- Render cards with: title, publisher, date, category, source type, authority band, relevance summary, URL, SDG tags.
- State clearly that links are for reference; Rivora AI does not endorse third parties and **does not replace official warnings**.

**Authority bands (display only; does not change risk scoring):**

| Band | Typical source_type | Meaning |
|---|---|---|
| `operational_authority` | `government` | National/state disaster or meteorological agencies (e.g. NDMA, IMD, SDMAs). Highest operational standing for public safety messaging. |
| `intergovernmental` | `un_agency` | UN / specialized agencies (e.g. UNDRR, WHO, WMO) — policy and guidance, not local official warnings. |
| `peer_reviewed` | `academic` | Journal articles, official reports with scholarly review. |
| `organizational` | `ngo` | Verified NGOs / foundations with public pages. Educational or programme context, not emergency authority. |
| `journalistic` | `news_outlet` | Reputable news reporting of events or policy. Clearly labeled as journalism. |
| `public_comms` | `social_media` or `org_public_page` | Official org websites, verified social posts, or campaign pages. Lowest evidential weight; included only if real, public, and directly relevant. |

### 1M1B and programme-context material
The internship is delivered in the **1M1B + AICTE + IBM SkillsBuild** ecosystem. The evidence layer **may** include 1M1B (One Million for 1 Billion) material, official social-media posts, or public organizational pages **only when all of the following are true**:
- The source is **real** (live public URL at curation time).
- The source is **publicly accessible** (no invented PDFs, private posts, or paraphrased “1M1B reports”).
- The source is **directly relevant** (SDGs, AI for sustainability, youth/community resilience, flood/climate preparedness, or the internship’s documented framing).
- The entry is labeled with authority band `organizational` or `public_comms` — **never** as government operational authority or peer-reviewed research unless the document actually is that.

**Do not fabricate 1M1B content**, quotes, statistics, certificates, social posts, or unpublished “internal” briefs. If no qualifying 1M1B URL can be verified at implementation time, omit 1M1B entries and document the omission in catalogue metadata. Optional verified starting points to check (not to invent around): `https://www.activate1m1b.org/`, official 1M1B LinkedIn, and IBM SkillsBuild / AICTE internship pages that actually exist.

### RAG grounding and attribution
- Conversational and explanation RAG must be **grounded in retrieved chunks**.
- Every grounded statement in the UI should carry **source attribution** (document title, category, section).
- Configurable **minimum similarity threshold** (default 0.35): below-threshold retrievals are discarded.
- If insufficient evidence is retrieved, the system must **explicitly say so** (standard no-relevant-information response). It must **not** fill gaps with ungrounded LLM prose.

### Hybrid intelligence (immutable tier)
- Deterministic risk engine **owns** the risk tier.
- IBM Granite **explains** the fixed result and generates preparedness guidance from engine outputs + RAG context.
- RAG grounds knowledge-based responses.
- Granite **must never** override, reclassify, “soften,” or invent a different risk tier. The tier is injected as a fixed fact in the prompt and displayed from the engine object, not from LLM text.

### Professional, presentation-ready UI
- Research-oriented information hierarchy: inputs → immutable result → uncertainty → explanation → actions → sources → disclaimer.
- Risk visualization (tier badge, score bar, factor contribution bars).
- Evidence/source cards with authority badges and filters.
- Preparedness recommendations as a distinct, numbered section.
- Uncertainty indicators that cannot be hidden.
- Persistent responsible-AI notices (what the system is **not**).
- Visual quality suitable for internship/research evaluation — not a default unstyled Streamlit demo.

### Responsible AI (programmatic, not cosmetic)
Preserve and enforce in code:
- Uncertainty handling (`INSUFFICIENT DATA` as a first-class tier; flags always shown).
- Source attribution on RAG-grounded outputs.
- Privacy protection (no exact addresses, personal names, or private location storage; PII-like patterns stripped).
- Hallucination safeguards (regex / pattern scan of LLM output for fabricated measurements and official-sounding warning language).
- Safety disclaimers injected **by code**, not left to the model.
- Human / government authority: users are directed to NDMA, State DMAs, IMD, and local emergency services for official decisions.

### Prohibited claims
Rivora AI **must not** claim or imply that it:
- issues **official flood warnings**;
- provides **exact flood predictions** or hydrological forecasts;
- authorizes **validated real-world emergency decisions**.

Known limitations (user-reported inputs, unvalidated scoring approximation, non-hyperlocal KB, probabilistic LLM text, scenario testing ≠ predictive accuracy) must appear in the UI and documentation.

### Evaluation metrics and impact numbers
- **Do not fabricate** accuracy percentages, F1 scores, lives-saved estimates, or real-world impact measurements.
- Test results may be reported **only after actual testing** (`pytest` or documented scenario runs).
- Distinguish clearly: prototype scenario tests vs validated predictive accuracy. The latter is **out of scope** for this prototype.

### Modularity and future data sources
Core modules (risk engine, RAG, LLM explainer, UI, evidence catalogue) remain independently replaceable. Design **adapter-shaped seams** (even if unused in v1) so later work can add weather APIs, geospatial layers, satellite flood-extent data, or other **validated** sources **without redesigning** scoring ownership, RAG contracts, or the UI result schema. v1 still uses user-reported structured inputs only.

---

## System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        Streamlit UI                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Risk         │  │ Conversational│  │ Evidence /           │ │
│  │ Assessment   │  │ Assistant    │  │ Sources              │ │
│  │ Panel        │  │ (RAG-only)   │  │ Panel                │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘ │
└─────────┼─────────────────┼─────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌───────────────────────────────────────────────────────────────┐
│                     Core Backend (Python)                     │
│                                                               │
│  ┌─────────────────────────┐  ┌────────────────────────────┐  │
│  │  Risk Assessment Engine │  │  RAG Pipeline              │  │
│  │  (Deterministic)        │  │  (LangChain + ChromaDB)    │  │
│  │  - Factor normalization │  │  - Document retrieval      │  │
│  │  - Weighted scoring     │  │  - Context assembly        │  │
│  │  - Tier classification  │  │  - Source attribution      │  │
│  │  - Uncertainty detection│  │                            │  │
│  └─────────────┬───────────┘  └──────────────┬─────────────┘  │
│                │                              │                │
│                ▼                              ▼                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LLM Explanation Layer                       │  │
│  │  (IBM Granite via WatsonxLLM)                            │  │
│  │  - Receives: fixed risk tier + contributing factors      │  │
│  │              + retrieved RAG context + uncertainty flags │  │
│  │  - Produces: human-readable explanation + prep actions   │  │
│  │  - Constrained prompt: cannot override the risk tier     │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────┐
│                   Knowledge Base                              │
│  /knowledge_base/                                             │
│  - Markdown documents (flood fundamentals, preparedness,      │
│    drainage, rural/agricultural, emergency, responsible AI)   │
│  /evidence_catalogue/                                         │
│  - sources.json (authority-banded; no fabricated entries)    │
└───────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Risk Assessment Flow
1. User submits environmental inputs via Streamlit form
2. `RiskEngine.score()` normalizes each factor and applies weighted scoring
3. Score maps to an immutable risk tier
4. Uncertainty flags are raised if critical inputs are missing or conflicting
5. Contributing factors are ranked and top drivers extracted
6. Tier + factors + uncertainty → assembled into a structured prompt context
7. RAG retrieves relevant preparedness documents from ChromaDB
8. Granite LLM generates explanation + recommendations using the constrained prompt
9. Full structured result (tier, factors, reasoning, uncertainty, actions, disclaimer) is displayed

### Conversational Assistant Flow
1. User asks a question in the chat panel
2. RAG pipeline retrieves top-k relevant knowledge-base documents
3. If no relevant documents found above threshold → system responds with explicit "no relevant information found" message
4. If relevant documents found → Granite LLM generates answer grounded strictly in retrieved context
5. Sources cited inline

### Evidence/Sources Flow
- `sources.json` is loaded and displayed in categorized, filterable, **authority-banded** cards
- Filters: category, source_type, authority_band
- No LLM involvement; purely static catalogue rendering
- 1M1B / programme-context entries appear only if curated from real public URLs and labeled `organizational` or `public_comms`

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding and Environment Setup

**Status:** `[ ]` pending

**Intent:**
Establish a clean, reproducible Python project structure with all dependencies, configuration files, and environment management in place before any logic is written.

**Expected Outcomes:**
- Directory structure matches the architecture
- `requirements.txt` captures all dependencies with pinned versions
- `.env.example` documents required environment variables
- `README.md` explains setup and run instructions
- `.gitignore` excludes secrets and generated artifacts

**Todo List:**
1. Create the top-level directory structure:
   ```
   rivora_ai/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py                  # Streamlit entrypoint
   │   ├── pages/
   │   │   ├── risk_assessment.py
   │   │   ├── assistant.py
   │   │   └── evidence.py
   │   ├── components/
   │   │   ├── risk_display.py
   │   │   ├── source_card.py
   │   │   └── disclaimer.py
   ├── core/
   │   ├── __init__.py
   │   ├── risk_engine.py           # Deterministic scoring
   │   ├── rag_pipeline.py          # LangChain + ChromaDB
   │   ├── llm_explainer.py         # Granite integration
   │   ├── knowledge_loader.py      # Markdown → ChromaDB ingestion
   │   └── responsible_ai.py        # Safety filters, disclaimer injection
   ├── knowledge_base/
   │   ├── flood_fundamentals.md
   │   ├── community_preparedness.md
   │   ├── drainage_infrastructure.md
   │   ├── rural_agricultural.md
   │   ├── river_hazards.md
   │   ├── emergency_guidance.md
   │   └── responsible_safety.md
   ├── evidence_catalogue/
   │   └── sources.json
   ├── vector_store/                # ChromaDB persisted data (git-ignored)
   ├── tests/
   │   ├── test_risk_engine.py
   │   ├── test_rag_pipeline.py
   │   ├── test_llm_explainer.py
   │   ├── test_responsible_ai.py
   │   └── scenarios/
   │       ├── normal_scenarios.json
   │       ├── high_risk_scenarios.json
   │       ├── insufficient_data_scenarios.json
   │       ├── conflicting_input_scenarios.json
   │       └── safety_hallucination_scenarios.json
   ├── .env.example
   ├── .gitignore
   ├── requirements.txt
   ├── README.md
   └── rivora-ai-plan.md
   ```
2. Write `requirements.txt` with: `streamlit`, `langchain`, `langchain-ibm`, `ibm-watsonx-ai`, `chromadb`, `sentence-transformers`, `python-dotenv`, `pydantic`, `pytest`
3. Write `.env.example` with: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `GRANITE_MODEL_ID`
4. Write `.gitignore` excluding: `vector_store/`, `.env`, `__pycache__/`, `.pytest_cache/`
5. Write `README.md` with: project purpose, setup steps, run instructions, responsible AI notice

**Relevant Context:**
- Fresh workspace; no existing code
- All paths are relative to `c:\Users\JOYEETA\RIVORA-AI\`

---

### Sub-Task 2 — Deterministic Risk Assessment Engine

**Status:** `[ ]` pending

**Intent:**
Build the transparent, auditable core of Rivora AI. This module is the single source of truth for risk classification. The LLM cannot override its output.

**Expected Outcomes:**
- `core/risk_engine.py` accepts structured environmental inputs
- Produces: risk tier, numeric score, ranked contributing factors, uncertainty flags
- All scoring logic is documented with comments explaining each weight and threshold
- Returns a typed `RiskAssessmentResult` Pydantic model

**Risk Factors and Weights (initial research-grounded design):**

| Factor | Input Type | Weight | Notes |
|---|---|---|---|
| Rainfall intensity | Categorical: low/moderate/heavy/extreme | 0.25 | Primary flood driver |
| Rainfall duration | Categorical: brief/sustained/prolonged | 0.15 | Saturation amplifier |
| Drainage condition | Categorical: good/partial/poor/blocked | 0.15 | Urban waterlogging amplifier |
| Previous flooding history | Boolean + severity | 0.15 | Historical vulnerability |
| Terrain/elevation | Categorical: elevated/flat/low-lying/depression | 0.10 | Runoff concentration |
| Current water accumulation | Categorical: none/minor/significant/severe | 0.10 | Real-time indicator |
| River hazard proximity | Categorical: none/distant/near/adjacent + level | 0.10 | Riparian risk |

**Risk Tier Thresholds:**
- INSUFFICIENT DATA: critical fields missing (rainfall intensity OR drainage condition OR terrain)
- LOW: score < 0.30
- MODERATE: 0.30 ≤ score < 0.55
- HIGH: 0.55 ≤ score < 0.75
- VERY HIGH: score ≥ 0.75

**Todo List:**
1. Define `RiskInput` Pydantic model with all factor fields, each as Optional with documented valid values
2. Define `RiskFactor` model: name, raw_value, normalized_score, weight, contribution
3. Define `RiskAssessmentResult` model: tier, numeric_score, ranked_factors, uncertainty_flags, has_insufficient_data
4. Implement `normalize_factor()` functions for each factor type
5. Implement `score()` method: iterate factors, compute weighted sum, detect insufficient data, classify tier
6. Implement `get_uncertainty_flags()`: identify missing, conflicting, or ambiguous inputs
7. Implement `rank_contributing_factors()`: sort by contribution descending
8. Write inline documentation for every threshold and weight decision

**Relevant Context:**
- Pydantic v2 for data models
- No LLM calls in this module; it must be fully testable without network access
- The tier produced here is passed read-only to `llm_explainer.py`

---

### Sub-Task 3 — Knowledge Base Documents

**Status:** `[ ]` pending

**Intent:**
Create the curated, authoritative Markdown knowledge base that feeds the RAG system. Each document covers a specific domain. Quality and factual grounding matter more than volume.

**Expected Outcomes:**
- 7 Markdown documents covering the full knowledge domain
- Each document has a front-matter header: `title`, `category`, `source_type`, `last_reviewed`
- Content is factual, citable, and avoids speculative claims **and fabricated statistics**; named figures require a catalogue-backed source
- Documents are chunked-friendly (clear section headings, moderate paragraph length)

**Document Topics:**
1. `flood_fundamentals.md` — how flooding and waterlogging occur, types of flooding, key physical drivers
2. `community_preparedness.md` — before/during/after flood actions, household readiness, communication
3. `drainage_infrastructure.md` — urban drainage, waterlogging causes, infrastructure vulnerability
4. `rural_agricultural.md` — impact on crops, soil, livestock, rural community vulnerability
5. `river_hazards.md` — river flooding, flash floods, dam/barrage considerations, riparian zones
6. `emergency_guidance.md` — evacuation principles, emergency contacts framework, first-response priorities
7. `responsible_safety.md` — AI limitations in emergency contexts, authoritative source guidance, responsible use

**Todo List:**
1. Write each Markdown document with front-matter and structured sections
2. Ensure content aligns with NDMA (India), WHO, UNDRR, and general international guidance where cited — citations must match real documents
3. Keep each document between 400–800 words for chunking efficiency
4. Include a "Key Points" summary section in each document for high-precision retrieval
5. Do not invent local flood statistics, casualty figures, or “case studies” that cannot be sourced

**Relevant Context:**
- Documents are ingested by `core/knowledge_loader.py` in Sub-Task 4
- ChromaDB chunk size will be approximately 512 tokens with 50-token overlap

---

### Sub-Task 4 — RAG Pipeline and Knowledge Loader

**Status:** `[ ]` pending

**Intent:**
Build the retrieval-augmented generation pipeline that loads knowledge base documents into ChromaDB and retrieves relevant context for both the risk assessment explainer and the conversational assistant.

**Expected Outcomes:**
- `core/knowledge_loader.py` ingests Markdown files, chunks them, embeds them, and persists to ChromaDB
- `core/rag_pipeline.py` retrieves top-k documents for a given query with similarity scores
- Pipeline enforces a minimum similarity threshold; below-threshold results are not returned **and must not be silently ignored in the UX** — the caller receives an empty set and must surface the standard “insufficient / no relevant evidence” message
- Source attribution (document title, category, section) is preserved in ChromaDB metadata and passed through to the UI
- Idempotent ingestion: re-running does not duplicate documents
- RAG never invents citations; if chunks are empty, the LLM is not asked to “best-effort” answer from parametric knowledge

**Todo List:**
1. Implement `KnowledgeLoader`: read Markdown files, extract front-matter metadata, split into chunks using LangChain `MarkdownTextSplitter`
2. Initialize ChromaDB persistent client pointing to `vector_store/`
3. Use `sentence-transformers/all-MiniLM-L6-v2` for local embeddings (via LangChain `HuggingFaceEmbeddings`)
4. Implement idempotency check using document hash stored in metadata
5. Implement `RAGPipeline`: accepts query string, returns list of `RetrievedChunk` objects with text, metadata, similarity score
6. Implement minimum similarity threshold (configurable, default 0.35)
7. Implement `build_context_string()`: formats retrieved chunks into a structured context block with source labels
8. Implement `no_relevant_context_response()`: standard, user-visible response when nothing clears the threshold (no fabricated citations)
9. Pass attributed chunk metadata through to both the explainer and the assistant so the UI can list sources used

**Relevant Context:**
- `sentence-transformers` runs locally; no API key needed for embeddings
- ChromaDB `PersistentClient` stores to `vector_store/` directory
- LangChain `Chroma` wrapper integrates with the embedding function

---

### Sub-Task 5 — IBM Granite LLM Integration and Explanation Layer

**Status:** `[ ]` pending

**Intent:**
Integrate IBM Granite via `langchain-ibm` WatsonxLLM. The LLM's role is strictly bounded: it receives an immutable risk tier, contributing factors, uncertainty flags, and RAG context, then generates a human-readable explanation and preparedness narrative. It cannot change the tier.

**Expected Outcomes:**
- `core/llm_explainer.py` initializes `WatsonxLLM` from environment variables
- Implements a constrained prompt template that explicitly passes the tier as fixed fact
- Generates: plain-language explanation, top contributing factor narrative, uncertainty acknowledgment, 5–7 preparedness actions, mandatory safety disclaimer
- **Does not emit a competing risk label**; if the model text mentions a different tier, `responsible_ai` flags it and the UI still shows the engine tier
- All outputs are returned as a typed `LLMExplanation` Pydantic model
- Implements graceful fallback if the LLM call fails (returns template-based explanation using deterministic data only), clearly labeled as fallback

**Prompt Architecture (constrained design):**
```
System context: You are Rivora AI, an AI-assisted flood risk interpretation assistant.
You do NOT determine risk levels. The risk level has been determined by a separate
deterministic risk assessment engine and is provided to you as a fixed fact.
Your role is to explain the risk assessment in plain language and provide
preparedness guidance grounded in the provided knowledge base context.

[FIXED RISK TIER: {tier}]
[RISK SCORE: {score}]
[TOP CONTRIBUTING FACTORS: {factors}]
[UNCERTAINTY FLAGS: {uncertainty_flags}]

[KNOWLEDGE BASE CONTEXT]
{rag_context}

[TASK]
1. Explain in plain language why this risk level was assessed, referencing the contributing factors.
2. If uncertainty flags are present, clearly state what information is missing and how it would affect the assessment.
3. Provide {n} specific preparedness actions appropriate for this risk level, grounded in the knowledge base context.
4. End with the mandatory safety disclaimer.
Do NOT invent environmental measurements, weather data, or official warnings not present in the input.
```

**Todo List:**
1. Implement `WatsonxLLM` initialization with model ID, parameters (temperature=0.3, max_new_tokens=600)
2. Implement `PromptTemplate` with the constrained architecture above
3. Implement `LLMChain` combining prompt + LLM
4. Implement `generate_explanation()`: accepts `RiskAssessmentResult` + RAG context, returns `LLMExplanation`
5. Implement output parsing: extract explanation sections into structured fields
6. Implement fallback: if LLM unavailable, compose explanation from templates using deterministic data
7. Log all LLM calls with input/output for auditability (no personal data logged)

**Relevant Context:**
- `langchain-ibm` provides `WatsonxLLM` and `WatsonxEmbeddings`
- Environment variables: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `GRANITE_MODEL_ID`
- Recommended Granite model: `ibm/granite-13b-instruct-v2` or `ibm/granite-3-8b-instruct`
- Temperature 0.3 keeps explanations consistent while allowing natural language variation

---

### Sub-Task 6 — Responsible AI Safeguards Module

**Status:** `[ ]` pending

**Intent:**
Implement a dedicated responsible AI layer that is called by every output path. This is not cosmetic — it programmatically enforces safety boundaries before any response is shown to the user.

**Expected Outcomes:**
- `core/responsible_ai.py` provides functions called by all output paths
- Disclaimer is injected programmatically, not left to the LLM
- Hallucination guard: output is scanned for fabricated measurement patterns before display
- Privacy: no exact addresses, personal names, or private location data are accepted or stored
- Input validation: inputs outside valid ranges are rejected with informative error messages

**Safeguards Implemented:**

| Safeguard | Mechanism |
|---|---|
| Official warning disclaimer | Injected programmatically into every risk result; text states Rivora AI is not an official warning or emergency decision system |
| Anti-hallucination scan | Regex patterns detect invented measurements/statistics and competing risk-tier language |
| Input sanitization | Strip PII patterns before processing |
| Uncertainty surfacing | Uncertainty flags always shown, never suppressed |
| Source attribution | Every RAG-grounded statement carries source label |
| Out-of-scope detection | Detects questions outside flood/preparedness domain in assistant |
| Fallback safety response | Template used when LLM output fails safety checks |

**Todo List:**
1. Implement `inject_disclaimer()`: prepends/appends mandatory safety text to every risk result
2. Implement `hallucination_guard()`: regex scan for fabricated number patterns, official-sounding claims
3. Implement `sanitize_input()`: remove PII-like patterns (email, phone, full addresses) from user text
4. Implement `validate_risk_input()`: check value ranges, required fields, conflicting values
5. Implement `detect_out_of_scope()`: keyword/embedding check for questions unrelated to flood preparedness
6. Implement `responsible_ai_notice()`: static function returning the system's AI capability statement
7. Write the mandatory disclaimer text covering: not an official warning system, contact NDMA/local authorities

**Relevant Context:**
- Called in `risk_engine.py`, `llm_explainer.py`, and `rag_pipeline.py`
- Disclaimer text must reference NDMA India, State Disaster Management Authorities, and local emergency services

---

### Sub-Task 7 — Evidence Catalogue

**Status:** `[ ]` pending

**Intent:**
Create the `sources.json` evidence catalogue that powers the Evidence/Sources panel. All entries must be real, verifiable sources. No fabricated statistics, articles, or affiliations.

**Expected Outcomes:**
- `evidence_catalogue/sources.json` contains structured source entries that are **real and URL-verifiable at curation time**
- Each entry has: `id`, `title`, `source_name`, `date`, `category`, `relevance_summary`, `url`, `source_type`, `authority_band`, `sdg_relevance`; optional `notes` (e.g. “journalism, not operational warning”)
- Categories: `official`, `research`, `news`, `informational`, `programme_context`
- Source types: `government`, `un_agency`, `academic`, `ngo`, `news_outlet`, `social_media`, `org_public_page`
- Authority bands: `operational_authority`, `intergovernmental`, `peer_reviewed`, `organizational`, `journalistic`, `public_comms` (see Non-Negotiable Requirements)
- 15–25 real, verifiable entries covering flood/preparedness domains **plus** zero or more 1M1B / IBM SkillsBuild / AICTE public pages **only if they pass the 1M1B inclusion rules**
- Mix must include government/disaster-management, peer-reviewed or formal research reports, and organizational/news as appropriate — **never** pad the catalogue with invented items to hit the count

**Example Entry Schema:**
```json
{
  "id": "src_001",
  "title": "National Disaster Management Guidelines: Management of Floods",
  "source_name": "National Disaster Management Authority (NDMA), India",
  "date": "2008",
  "category": "official",
  "source_type": "government",
  "relevance_summary": "Official Indian government framework for flood management, preparedness, and community response protocols.",
  "url": "https://ndma.gov.in/",
  "sdg_relevance": ["SDG 11", "SDG 13"],
  "authority_band": "operational_authority",
  "notes": "Official government guidance. Not a live warning feed."
}
```

**1M1B example (include only if the URL is confirmed live and the page is genuinely 1M1B):**
```json
{
  "id": "src_1m1b_001",
  "title": "<exact page title from the live site>",
  "source_name": "1M1B (One Million for 1 Billion)",
  "date": "<date shown on the page, or year if no day is published>",
  "category": "programme_context",
  "source_type": "ngo",
  "authority_band": "organizational",
  "relevance_summary": "<one sentence describing what THIS page actually says about SDGs / AI for sustainability — not invented programme metrics>",
  "url": "https://www.activate1m1b.org/",
  "sdg_relevance": ["SDG 11", "SDG 13"],
  "notes": "Programme/organizational context. Not disaster-management authority and not peer-reviewed research."
}
```
If `activate1m1b.org` or a candidate social post cannot be verified, **do not** keep a placeholder entry.

**Todo List:**
1. Research and compile 15–25 real sources from: NDMA India, SDMAs, IMD, UNDRR, WHO/WMO, peer-reviewed or formal technical reports, reputable news archives
2. Independently check 1M1B / IBM SkillsBuild / AICTE **public** pages or official social posts; include only those that are live, attributable, and relevant; label `programme_context` + `organizational` or `public_comms`
3. Assign `category`, `source_type`, and `authority_band` correctly — never upgrade a social post to `operational_authority` or `peer_reviewed`
4. Write `sources.json` with full schema for each entry; no invented URLs or titles
5. Validate URLs against real domains (live availability can still change later; record `last_checked` in catalogue metadata)
6. Add `catalogue_metadata`: version, last_updated, last_checked, total_entries, `includes_1m1b` boolean, and a one-line note if 1M1B was omitted for lack of a verifiable URL

**Relevant Context:**
- No LLM is used to generate or verify these entries — all are manually curated
- The Evidence panel renders these as cards; no dynamic generation

---

### Sub-Task 8 — Streamlit UI

**Status:** `[ ]` pending

**Intent:**
Build a **professional, presentation-ready** Streamlit interface (research-oriented, not a beginner demo). Clear information hierarchy, risk visualization, evidence/source cards with authority bands, preparedness recommendations, uncertainty indicators, and responsible-AI notices.

**Expected Outcomes:**
- `app/main.py`: application entry, navigation, sidebar with system description and responsible AI notice
- `app/pages/risk_assessment.py`: structured input form + full risk result display
- `app/pages/assistant.py`: conversational RAG assistant with source citations
- `app/pages/evidence.py`: filterable, categorized evidence catalogue cards
- `app/components/`: reusable display components
- Professional visual design using Streamlit theming + custom CSS (consistent typography, spacing, and a restrained research palette — not default “rainbow demo” widgets without hierarchy)

**UI Structure:**

**Sidebar:**
- Rivora AI logo/title
- One-line system description
- Responsible AI notice (what the system is NOT)
- Link to Evidence/Sources page

**Risk Assessment Page:**
- Section 1: Input form (organized into logical groups: Rainfall, Terrain, Drainage, Water State, River Hazards, Community Context)
- Section 2: Risk Result (risk tier badge with color coding, numeric score bar, top contributing factors with individual bars). **Tier and score are bound to `RiskAssessmentResult` from the engine, never parsed from Granite text.**
- Section 3: Uncertainty indicators (flags and INSUFFICIENT DATA callouts always visible when present)
- Section 4: AI Explanation (Granite-generated narrative only; if LLM fallback/template is used, label it as such)
- Section 5: Preparedness Actions (numbered, actionable list)
- Section 6: Source Attribution (which RAG documents informed the response; empty-state copy if none retrieved)
- Section 7: Safety Disclaimer (always visible, styled distinctively; states the system is not an official warning or emergency decision tool)

**Assistant Page:**
- Chat interface with message history
- "Grounded in knowledge base" indicator
- Sources cited per response
- Clear "No relevant information found" state when applicable
- Suggested starter questions

**Evidence Page:**
- Filter by category, source type, and **authority band**
- Cards showing: title, source, date, relevance summary, link, category badge, **authority-band badge**
- Optional `programme_context` filter for verified 1M1B / SkillsBuild / AICTE public material
- Total count display
- Note that external links are provided for reference; Rivora AI does not endorse them and does not issue official warnings

**Todo List:**
1. Configure Streamlit page config: title, icon, layout=wide
2. Implement sidebar with system description and responsible AI notice
3. Implement risk assessment input form with grouped fields and helpful tooltips
4. Implement risk result display components: tier badge, score bar, factor bars
5. Implement explanation display with uncertainty section highlighted
6. Implement preparedness actions display as numbered cards
7. Implement disclaimer component styled distinctively
8. Implement chat interface for assistant page with session state message history
9. Implement evidence catalogue page with filter controls and source cards
10. Apply consistent styling: professional color palette, readable typography

**Relevant Context:**
- Risk tier colors: LOW=green, MODERATE=amber, HIGH=orange, VERY HIGH=red, INSUFFICIENT DATA=grey
- Streamlit `st.session_state` manages conversation history
- Use `st.columns`, `st.expander`, `st.metric`, `st.progress` for structured layouts

---

### Sub-Task 9 — Test Suite

**Status:** `[ ]` pending

**Intent:**
Build a serious, structured test suite that validates the system's correctness, safety, and responsible AI properties. Explicitly avoids invented accuracy percentages. Tests are scenario-based.

**Expected Outcomes:**
- `tests/test_risk_engine.py`: unit tests for all scoring pathways
- `tests/test_rag_pipeline.py`: retrieval quality tests
- `tests/test_llm_explainer.py`: prompt constraint tests (mocked LLM)
- `tests/test_responsible_ai.py`: safety filter and disclaimer injection tests
- `tests/scenarios/`: JSON test scenario files
- Test report template that clearly distinguishes prototype scenario testing from validated predictive accuracy
- **No invented accuracy percentages or impact metrics** in tests, README, or UI. Numeric test outcomes appear only after `pytest` (or equivalent) has actually been run

**Test Categories:**

| Category | What is tested |
|---|---|
| Normal scenarios | Typical moderate-risk community inputs produce expected tier and explanations |
| High-risk scenarios | Extreme rainfall + poor drainage + river proximity produces VERY HIGH |
| Insufficient data | Missing critical fields produce INSUFFICIENT DATA, not a false LOW |
| Conflicting inputs | Minor rainfall + severe current water accumulation handled correctly |
| Hallucination tests | LLM output scanned for fabricated measurements not present in input |
| Safety boundary tests | System never claims to be an official warning service |
| RAG grounding tests | Responses contain only knowledge-base-backed claims |
| Explainability tests | Every risk result includes ranked factors and numeric contributions |
| Edge cases | All-minimum inputs, all-maximum inputs, single-factor inputs |

**Todo List:**
1. Write `normal_scenarios.json` with 5 representative community scenarios
2. Write `high_risk_scenarios.json` with 5 severe-condition scenarios
3. Write `insufficient_data_scenarios.json` with 5 missing-data patterns
4. Write `conflicting_input_scenarios.json` with 5 conflicting-value combinations
5. Write `safety_hallucination_scenarios.json` with test prompts designed to elicit unsafe responses
6. Write `test_risk_engine.py` covering all tiers and boundary conditions
7. Write `test_rag_pipeline.py` covering retrieval, threshold filtering, and no-result handling
8. Write `test_llm_explainer.py` with mocked LLM to verify prompt structure and output parsing
9. Write `test_responsible_ai.py` covering all safeguard functions
10. Document testing methodology and limitations clearly in `README.md`
11. After tests are run, record pass/fail counts factually; never pre-write “95% accuracy” or similar claims

**Relevant Context:**
- Use `pytest` as the test runner
- LLM is mocked in unit tests to avoid API dependency
- Scenario JSON files serve as both tests and demonstration inputs

---

### Sub-Task 10 — Documentation and Future Expansion Notes

**Status:** `[ ]` pending

**Intent:**
Ensure the project is fully documented for internship evaluation, potential research expansion, and future developers. Documentation is part of the deliverable.

**Expected Outcomes:**
- `README.md`: complete setup, run, and architecture explanation
- Inline code documentation: every module, class, and function has a docstring
- `ARCHITECTURE.md`: deeper technical architecture reference
- `FUTURE_WORK.md`: structured roadmap for research expansion, including **adapter interfaces** (weather, geospatial, satellite, validated ML) that plug into the existing `RiskInput` / result schema without replacing the deterministic engine as the v1 classifier
- `RESPONSIBLE_AI.md`: standalone responsible AI statement, including prohibited claims (no official warnings, no exact predictions, no validated emergency decisions)

**Future Expansion Roadmap (documented in FUTURE_WORK.md):**

| Phase | Capability | Technical Path |
|---|---|---|
| Phase 2 | Real-time weather API integration | OpenWeatherMap / IMD API **connector module** implementing a documented input adapter into `RiskInput` |
| Phase 3 | Geospatial risk mapping | QGIS / Folium integration, DEM data ingestion via a geo adapter — UI map panel additive, not a core rewrite |
| Phase 4 | Satellite imagery analysis | Sentinel-2 / NASA MODIS flood extent layers as optional evidence/context, not as a silent override of the engine |
| Phase 5 | Validated ML risk model | Labeled flood event dataset, scikit-learn / XGBoost **behind the same result contract**; engine remains default until validation exists |
| Phase 6 | Community observation reports | Structured community input form, moderation layer |
| Phase 7 | Multilingual support | LLM translation layer, regional language knowledge base |
| Phase 8 | Mobile interface | Streamlit Cloud deployment or React Native frontend |

**Todo List:**
1. Write complete `README.md` with setup, run, architecture summary, test instructions
2. Write `ARCHITECTURE.md` with module descriptions, data flow, design decisions
3. Write `FUTURE_WORK.md` with phased roadmap table and research directions
4. Write `RESPONSIBLE_AI.md` covering all 10 responsible AI dimensions
5. Ensure all Python modules have complete docstrings

---

## What Makes Rivora AI Technically Distinctive

1. **Hybrid intelligence architecture**: deterministic scoring is the authoritative classifier; the LLM is bounded to explanation only — this is not how most flood chatbots work
2. **Immutable risk tier**: the LLM prompt explicitly receives the tier as a fixed fact and is instructed it cannot change it — hallucination of risk levels is architecturally prevented
3. **Explainability by design**: every risk assessment returns a ranked factor breakdown with numeric contributions, not just a label
4. **Uncertainty-aware**: INSUFFICIENT DATA is a first-class output, not a fallback; missing inputs are surfaced and explained
5. **RAG-only conversational grounding**: the assistant cannot generate free responses — it is strictly bounded to the knowledge base, with an explicit no-result state and source attribution
6. **Programmatic responsible AI**: disclaimers and safety filters are code-enforced, not prompt-requested; government authority is never impersonated
7. **Evidence separation and integrity**: the evidence catalogue is statically curated, authority-banded, and manually verified — including optional real 1M1B/public programme sources — and cannot be polluted by LLM generation or fabricated URLs
8. **Modular architecture**: every layer (risk engine, RAG, LLM, UI) is independently replaceable, with adapter seams for future weather APIs, geospatial data, satellite layers, and validated models

---

## How to Demonstrate the Prototype Effectively

1. **Open with the architecture diagram** — show the hybrid intelligence design before any demo
2. **Run the high-risk scenario first** — extreme rainfall + blocked drainage + river adjacency → VERY HIGH with full explanation
3. **Show the INSUFFICIENT DATA path** — demonstrate the system refuses to classify when critical inputs are missing
4. **Run a conflicting-input scenario** — demonstrate uncertainty flag surfacing
5. **Switch to the Assistant** — ask "What should I do before a flood?" → show RAG-grounded response with source citations
6. **Show the Evidence page** — curated cards with authority bands (government vs research vs news vs optional verified 1M1B programme context)
7. **Show the Responsible AI notice** — explicitly walk evaluators through what the system claims NOT to do
8. **Show the test results** — run `pytest` live to demonstrate scenario test coverage
9. **Close with the Future Work roadmap** — demonstrate research scalability

---

## Security and Privacy Considerations

- No personal data is collected or stored by the system
- Input sanitization removes PII-like patterns before processing
- The `.env` file (API keys) is excluded from version control
- ChromaDB vector store contains only public knowledge-base content, no user data
- No conversation history is persisted across sessions
- All LLM API calls go to IBM watsonx.ai — no third-party LLM services

---

## Known Limitations (to be stated explicitly in the UI and documentation)

- Risk assessment is based on user-reported inputs, not real-time sensor or satellite data
- The deterministic scoring model is a structured approximation, not a validated hydrological model
- Knowledge base reflects general guidance; it does not account for hyperlocal geographic specifics
- IBM Granite explanations are probabilistic and may occasionally be imprecise despite prompt constraints
- The system has not been validated against a labeled real-world flood event dataset
- Prototype testing with scenarios is not equivalent to validated predictive accuracy; **no accuracy % is claimed until tests are actually run and only those results are reported**
- The Evidence catalogue URLs are provided for reference; live availability is not guaranteed
- The system does not issue official flood warnings, exact flood predictions, or authorized emergency decisions

---

## Relevant SDG Alignment

| SDG | How Rivora AI contributes |
|---|---|
| SDG 11.5 | Reduces disaster risk through community-level preparedness information |
| SDG 13.1 | Strengthens resilience and adaptive capacity to climate-related hazards |
| SDG 6.6 | Raises awareness of water-related ecosystem vulnerability |

---

## Recommended implementation order (after approval)

Do **not** start this sequence until the user explicitly approves implementation. Then:

1. Project scaffolding and environment (Sub-Task 1)
2. Responsible AI module (Sub-Task 6) — used by later paths
3. Deterministic risk engine (Sub-Task 2) + engine tests / scenario JSON
4. Knowledge-base Markdown (Sub-Task 3) — no fabricated statistics
5. Evidence catalogue (Sub-Task 7) — real URLs, authority bands, optional verified 1M1B
6. RAG pipeline and knowledge loader (Sub-Task 4)
7. IBM Granite explanation layer (Sub-Task 5) — requires watsonx credentials for live calls
8. Streamlit UI (Sub-Task 8) — presentation-ready
9. Full test suite (Sub-Task 9) — report results only after runs
10. Documentation (Sub-Task 10)

**External configuration still required for live Granite:** `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `GRANITE_MODEL_ID` in a local `.env` (never committed). Embeddings remain local.

**Implementation status:** no application code exists yet; this file is the only project artifact until implementation is approved.
