# CA AI Assistant

A working local educational MVP for Indian CA students, beginning with **CA Intermediate Advanced Accounting / depreciation**. It combines Streamlit, an optional OpenAI model, private PDF retrieval and explicit Decimal calculation tools.

**No key is required for the offline app.** Live model responses need configured credentials and explicit API-spending enablement. This is an independent educational project, not an official ICAI solution service. See [the final project report](docs/FINAL-PROJECT-REPORT.md) for actual verification and remaining blockers.

## Start on Windows

Open this directory in VS Code, then use PowerShell:

```powershell
Set-Location 'C:\Users\ADMIN\AI Assistant\ca-ai-assistant'
# Only create the environment if it does not already exist:
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Visit **http://localhost:8501**. Stop with **Ctrl+C**. The supplied environment already contains the required packages on this machine, so you can run the last command directly. Calling the environment's Python explicitly avoids PowerShell activation-policy changes.

In VS Code select **Python: Select Interpreter → .venv\Scripts\python.exe**. Install Microsoft **Python**, **Pylance** and **Python Debugger**; the workspace includes recommendations and an F5 Streamlit launch configuration. Details are in the [VS Code Python tutorial](https://code.visualstudio.com/docs/python/python-tutorial).

## What works

- CA level, subject, chapter, examination-attempt and answer-format settings.
- English and optional model-generated Tamil explanations.
- Session chat, feedback, context snapshots and JSON downloads.
- Clearly labelled demo mode and the original prepared answer preview.
- OpenAI Responses API with conversation context, structured outputs, timeouts, bounded retries and safe errors.
- Authorized PDF ingestion with page numbers, layout-oriented text extraction, optional OCR, metadata, replacement and deletion.
- Persistent extracted text and vectors in SQLite; scoped FAISS similarity search.
- An explicit cosine-search fallback when native FAISS cannot load.
- OpenAI semantic embeddings when configured, or a labelled offline keyword-vector baseline.
- Source IDs and exact quotation validation; insufficient-evidence responses.
- Straight-line, partial-year, reducing-balance and prospective revised-estimate depreciation.
- API request limits, conservative cost reservations and an optional shared-password access gate.
- Offline evaluation, opt-in live model evaluation, CI, container configuration and a gated tuning pipeline.

The menu is an extensible study catalogue, not a complete verified ICAI syllabus. Other subjects have model/retrieval architecture but no independently validated subject-specific calculation engine. Tax and law answers require applicable uploaded evidence.

## Enable real AI

Copy the template once:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

Edit the ignored `.env` locally:

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-6.1-terra
OPENAI_API_KEY=YOUR_PRIVATE_KEY
ALLOW_PAID_API=true
EMBEDDING_BACKEND=openai
DAILY_BUDGET_USD=1
INPUT_PRICE_PER_MILLION=1
OUTPUT_PRICE_PER_MILLION=5
EMBEDDING_PRICE_PER_MILLION=0.02
```

Replace the key placeholder; never paste the real key into chat or commit it. Restart Streamlit, then enable **provider consent** in the sidebar before sending questions or passages. This allows paid requests and sends the selected content to OpenAI. Keep `EMBEDDING_BACKEND=local` to use the offline retrieval baseline with model-generated answers.

Configuration precedence is process environment, then Streamlit cloud secrets, then `.env`. A different model requires explicit current input/output prices. The adapter uses the [Responses API](https://developers.openai.com/api/docs/quickstart), structured output and an allowlisted calculation function. Live API correctness has not been verified without credentials.

## Solve the changed-value example

In the default Intermediate / Advanced Accounting / depreciation context, ask:

> Annual straight-line depreciation: cost 850000, residual value 50000, useful life 8 years.

The local calculation engine produces **INR 100000.00** and shows its inputs, substitutions and closing carrying amount. For six months, explicitly say **for 6 months**. The **Calculations** tab provides a reliable form for all supported methods.

The parser deliberately requires explicit facts. Missing residual value, method or period leads to clarification. Dates require an agreed day/month convention. Impairment, revaluation, disposal, statutory rates, units-of-production and complex accounting treatments are outside the validated engine. An ambiguous follow-up should supply the complete revised inputs.

Calculations use Decimal with half-up rounding to two decimals. They verify arithmetic under stated assumptions; they do not prove that a method is appropriate to a particular accounting standard.

## Add your knowledge base

1. Choose the level, subject, chapter and **exact examination attempt**.
2. Open **Study library** and confirm processing rights.
3. Upload a PDF; enter its title, source edition and publication date.
4. Enter effective dates and the sidebar year fields for tax/law material.
5. Use **Process and index PDF**. Review extraction warnings.
6. Ask a question in the matching study context, optionally requiring source evidence.
7. Expand **Sources and answer status** to inspect document, chapter, edition, pages and quoted evidence.

Use **Replace** when updating the same document; the old version remains intact if processing fails. **Remove this document** deletes its stored text and vectors. Changing embedding models requires reindexing; vectors from different models are not mixed.

Defaults: 10 MB per file, 150 pages, 20 documents per session, 2 million extracted characters per document and 5,000 matching sections per retrieval. Long questions/solutions can span chunks; extraction preserves text layout where possible but is not a mathematical/table understanding engine.

Original PDF bytes are not retained. Extracted text and vectors are stored in ignored `data/knowledge.sqlite`. Each anonymous Streamlit session has its own workspace ID. A refresh can lose access to that ID even though the server data remains; this is not an account-based durable student library. See [storage and deployment guidance](docs/DEPLOYMENT.md) before multi-user hosting.

For an original, redistributable PDF to try:

```powershell
.\.venv\Scripts\python.exe -m scripts.create_sample_pdf
```

Upload `data/sample-depreciation.pdf`. Its notes are authored for this project and marked CC0. No ICAI book is bundled.

For OCR:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

Install the Tesseract executable separately and put it on PATH, then enable the OCR checkbox. The optional OCR adapter is tested with a substitute recognizer; real Tesseract OCR has not been executed here. Verify every extracted figure against the PDF.

## Source and applicability rules

Documents are filtered by workspace, level, subject, chapter and declared attempt **before** ranking. Timeless conceptual notes can span attempts; tax/law notes cannot. Tax/law requires a matching assessment/financial year and effective date.

A source-linked model claim must contain a known source ID and an exact matching quotation. Unsupported references are rejected. This checks citation identity and evidence text, **not semantic entailment**. The model can still misunderstand a valid passage. Uploader-supplied metadata is not automatically verified against ICAI or statutory publications.

Uploaded text is untrusted data, not system instructions. The application never executes student-supplied or model-generated Python.

## Test and evaluate

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m evaluation.evaluate
.\.venv\Scripts\python.exe -m scripts.check_release
```

The original 22 Phase 1 tests are retained. The evaluation dataset contains **84 original cases**: 60 numerical, 8 missing-input/scenario cases, 8 concept-retrieval cases and 8 source checks. Numerical expectations come from an independent Fraction implementation, not the production calculator.

Offline scores do not measure live-model conceptual reasoning. The concept cases test retrieval against original notes; specialist review remains necessary. The live evaluator is opt-in:

```powershell
.\.venv\Scripts\python.exe -m evaluation.model_run --allow-paid-api --limit 5 --output data/evaluation/model-baseline.json
```

This requires enabled credentials and incurs API usage. It reports automatic tool/citation contracts and saves responses for human review. Compare results only for the same case set and evaluation mode:

```powershell
.\.venv\Scripts\python.exe -m evaluation.compare data/evaluation/model-baseline.json data/evaluation/model-candidate.json
```

The Windows browser smoke script uses an isolated headless Chrome profile and an original sample PDF:

```powershell
.\.venv\Scripts\python.exe -m scripts.browser_smoke
```

It requires Chrome at the path in the script. It closes its test server and browser when finished.

## Project map

| Path | Purpose |
| --- | --- |
| `app.py`, `ui/` | Dashboard, library, workbench, runtime and optional access gate |
| `config/catalog.py`, `config/settings.py` | Study navigation and validated server configuration |
| `backend/ai_engine.py`, `providers.py` | Reasoning workflow, bounded conversation and provider adapter |
| `backend/calculator.py`, `solver.py` | Decimal procedures and conservative question recognition |
| `backend/document_processor.py` | Page-aware PDF extraction, chunking and optional OCR |
| `backend/embeddings.py`, `retrieval.py` | Embedding modes, private storage and vector search |
| `backend/citations.py`, `syllabus_versions.py` | Evidence validation and applicability filters |
| `backend/session.py`, `usage.py` | Session records, exports, API limits and cost reservations |
| `evaluation/` | Original cases, independent oracle and evaluation/comparison commands |
| `training/` | Reviewed-data preparation and optional Vertex tuning/inference scripts |
| `tests/` | Regression, integration, security and pipeline tests |
| `scripts/` | Health, release, browser and sample-material helpers |
| `.github/workflows/tests.yml` | Offline Linux CI; requires native FAISS there |
| `Dockerfile`, `compose.yaml` | Non-root container and local persistent-volume template |
| `.env.example`, `.streamlit/secrets.example.toml` | Blank/default configuration, never real credentials |
| `docs/DEPLOYMENT.md`, `docs/TRAINING.md` | Deployment and model-customization instructions |
| `docs/FINAL-PROJECT-REPORT.md` | Actual status, results, limitations and remaining approvals |

## GitHub, hosting and model customization

Follow [deployment instructions](docs/DEPLOYMENT.md) to create a private GitHub repository, push, configure cloud secrets and deploy. No remote or public URL is claimed until a real deployment succeeds.

Follow [training instructions](docs/TRAINING.md) only after evaluating the RAG baseline. RAG retrieves material; fine-tuning changes model behavior from examples; continued pretraining consumes additional domain text; training from scratch creates a new foundation model. Only the optional fine-tuning preparation/submission workflow is implemented.

## Troubleshooting

| Issue | Action |
| --- | --- |
| No AI reply | Check provider, key, `ALLOW_PAID_API=true` and sidebar consent. |
| API budget reached | Inspect reservations and actual provider billing; adjust only within your authorized budget. |
| No applicable sources | Match chapter/attempt/year/date; reindex after changing embedding models. |
| Upload is disabled | Confirm processing rights; semantic indexing also needs provider consent. |
| FAISS DLL blocked on Windows | The app uses its labelled cosine fallback. Do not disable Windows policy; validate native FAISS on the deployment host. |
| Tables/formulas extract badly | Review the PDF, use optional OCR where appropriate, and correct authorized source material. |
| Session disappears | History and anonymous identity are session-local; export before leaving. |
| Port is busy | Add `--server.port 8502` and open that port. |
| Hosted app refuses to start | Configure a strong `APP_PASSWORD` when `REQUIRE_PASSWORD=true`. |
