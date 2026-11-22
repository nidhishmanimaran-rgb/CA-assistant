# CA AI Assistant — final project report

Date: 2026-11-22 (Asia/Calcutta)

## Status

Phase 1 is preserved and complete. Phases 2–4 and local Phase 8 are implemented and tested. Phase 5 is GitHub, Streamlit, and Docker ready but not deployed. Phase 6 is complete for the offline MVP evaluation. Phase 7 has a tested preparation/submission pipeline but no real training run. Production deployment, live model accuracy, OCR, and expert validation remain external work.

## Implemented

Configurable demo/OpenAI provider with secrets, timeouts, safe errors, structured responses, context, consent, and usage limits. Decimal-safe depreciation tools cover straight-line, reducing-balance, and revised estimates. Authorized PDF ingestion provides page-aware extraction, optional OCR adapter, applicability metadata, private SQLite/vector storage, duplicate replacement, session scoping, validated citations, and FAISS or labelled Python fallback retrieval. The UI includes English and optional Tamil provider mode, library/calculation tabs, feedback, download, password gate, responsive layout, health check, Docker/Compose, GitHub Actions, evaluation, and training utilities.

## Verification

- python -m pytest -q: **170 passed**, including the original 22 regression tests.
- Offline evaluation: **84/84** (60 numerical, 8 missing-information, 8 concept retrieval, 8 source-grounding).
- scripts.check_release: passed; 36 Python files parsed.
- pip check: passed.
- Browser smoke: passed health, changed-value depreciation (850000, 50000, 8 -> 100000), authorized sample PDF ingestion, [S1] retrieval, chat JSON download with source metadata, and 390px mobile overflow.
- Live AI accuracy was not measured because no provider key was available. Offline scores do not claim general accounting accuracy.

## Blockers and limitations

No OpenAI, Google, GitHub, or cloud credentials were present; no paid call, deployment, or tuning job was made. Native FAISS is blocked by this Windows Application Control policy, so the tested pure-Python fallback is active locally. OCR/Tesseract was unavailable. Anonymous sessions and local data are not durable; production needs authenticated accounts, managed storage, worker isolation for hostile PDFs, distributed limits, and centralized secrets/logging. The solver is a narrow verified depreciation MVP; tax, law, and broader accounting need dated reviewed sources.

## Security and cost

Secrets, PDFs, SQLite/vector data, training data, and exports are ignored. Keys are not hardcoded or logged. Provider calls require consent and paid mode. Inputs, PDF limits, citations, models, and tool operands are validated. No paid usage occurred. Planning prices are GPT-6.1 Terra $1/M input, $5/M output, and $0.02/M embeddings; actual cost varies with context and retries.

## Launch and public deployment

    cd "C:\\Users\\ADMIN\\AI Assistant\\ca-ai-assistant"
    .\\.venv\\Scripts\\Activate.ps1
    pip install -r requirements-dev.txt
    Copy-Item .env.example .env
    streamlit run app.py

For public deployment, push to GitHub, configure Streamlit secrets or container secrets, set a strong APP_PASSWORD, review ALLOW_PAID_API and budgets, and add durable storage/authentication before private uploads. Never commit books, .env, or secrets.toml.
