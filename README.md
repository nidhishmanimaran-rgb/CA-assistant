# CA AI Assistant — Phase 1

A local Streamlit study workspace for a progressively built CA tutor. **Phase 1 is
an interface demo:** it does not call a model, answer arbitrary accounting
questions, ingest PDFs, retrieve sources, calculate new figures, or train anything.
The first planned subject is **CA Intermediate Advanced Accounting**, starting with
**property, plant and equipment / depreciation**. This is an independent project,
not an official ICAI product or a production-ready tutor.

## What works now

- CA level, subject, chapter, attempt label, English language and three answer modes.
- Demo chat with a frozen copy of the study settings on each message.
- A separately requested, clearly labelled prepared depreciation example.
- Session history, clear chat, thumbs feedback, JSON chat export and local issue export.
- A visible, disabled PDF uploader for Phase 3.
- Native Streamlit theme selection, VS Code debugging and automated tests.

Foundation, Final, other subjects and non-MVP chapters are **UI previews**.
The course catalogue is not a complete or attempt-verified ICAI syllabus.
Tamil is planned; the language selector currently supports English only.
The attempt field is a label, not a verified examination calendar or amendment filter.

## Folder structure and purpose

```text
ca-ai-assistant/
├── app.py                         # Streamlit dashboard and widget callbacks
├── backend/
│   ├── __init__.py
│   ├── demo.py                    # Explicit demo responses and fixed example
│   └── session.py                 # Context, validation, bounded history and export
├── config/
│   ├── __init__.py
│   └── catalog.py                 # Small UI catalogue and limits
├── knowledge_base/
│   └── README.md                  # Private-material policy; no documents yet
├── tests/
│   ├── test_app.py                # Streamlit interaction tests
│   └── test_session.py            # Validation, history and honest-demo tests
├── docs/
│   ├── phase-1-checklist.md        # Manual acceptance checks
│   └── phase-2-plan.md             # Next-phase design only
├── .streamlit/
│   └── config.toml                # Loopback server, theme and privacy settings
├── .vscode/
│   ├── extensions.json            # Extension recommendations
│   ├── launch.json                # F5 launches Streamlit
│   └── settings.json              # Virtual environment and test discovery
├── .env.example                   # Empty future-provider variable names
├── .gitignore                     # Excludes credentials, documents and local data
├── pyproject.toml                 # Pytest configuration
├── requirements.txt               # Pinned Streamlit runtime
├── requirements-dev.txt           # Runtime plus test runner
└── README.md
```

The virtual environment `.venv/` and local Git metadata `.git/` are generated
during setup and are not source files. Later phases will add actual AI, retrieval,
document-processing, calculator and evaluation modules when they are implemented.

## VS Code and prerequisites

Use **Python 3.11** for the tested setup and install [VS Code](https://code.visualstudio.com/)
and [Git for Windows](https://git-scm.com/downloads/win) if missing.
In VS Code choose **File → Open Folder** and open this `ca-ai-assistant` directory.

Install these Microsoft extensions from the Extensions panel:

| Extension | Identifier | Purpose |
| --- | --- | --- |
| Python | `ms-python.python` | Python editing, environments and tests; required for this VS Code workflow |
| Pylance | `ms-python.vscode-pylance` | Type hints and completion; recommended |
| Python Debugger | `ms-python.debugpy` | F5 debugging; required to use the supplied launch configuration |

VS Code should offer these workspace recommendations. Git support is built in.
See the [official Python tutorial](https://code.visualstudio.com/docs/python/python-tutorial).

## Windows setup

Open **Terminal → New Terminal** in VS Code and select PowerShell. From the parent workspace:

```powershell
Set-Location 'C:\Users\ADMIN\AI Assistant\ca-ai-assistant'
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

If the environment is already supplied and working, skip recreating it and
reinstalling dependencies. A virtual environment keeps this project's packages
separate from other Python projects.

These commands deliberately call the environment's Python directly, so they work
even when PowerShell does not allow activation scripts. Optional activation is:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked, keep using the full Python path; changing your execution
policy is unnecessary. If `py` is unavailable, use `python -m venv .venv` after
checking `python --version`.

Press **Ctrl+Shift+P → Python: Select Interpreter** and select
`.venv\Scripts\python.exe`. The workspace includes a default interpreter path.

### Environment variables

Phase 1 requires **no API key** and does **not load `.env`**. To prepare a local
template for the next phase, copy it once:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

Keep all values blank for now. Real credentials must never be put into
`.env.example`, frontend code, screenshots, chat exports or Git.
The current application does not read these variables, even if populated.

### Dependencies

`requirements.txt` contains:

```text
streamlit==1.67.0
```

`requirements-dev.txt` adds `pytest>=8.3,<10`. We avoid installing AI SDKs,
vector databases, PDF libraries or OCR tooling before their phases.
Streamlit 1.67.0 is the selected release according to its
[official release notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2026).
The direct runtime dependency is pinned; transitive dependencies are resolved by
pip. A full lock across deployment targets will be addressed before hosting.

## Run locally

From this project directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open **http://localhost:8501**. Stop the server with **Ctrl+C** in the terminal.
Alternatively, press **F5** in VS Code and choose **CA AI Assistant: Streamlit**.
Do not launch this app with the editor's plain “Run Python File” button.

The server listens on `127.0.0.1` for local development. Theme selection is in
Streamlit's top-right menu → **Settings → Theme**. The interface uses native widgets
and a static responsive header; no external assets or fonts are needed.

## Verify Phase 1

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
```

The tests use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing),
which runs the app and simulates widget interactions. They check session
isolation, selector changes, context snapshots, input limits, history bounds,
exports and the distinction between demo acknowledgements and fixed examples.
They do **not** measure AI correctness, retrieval quality or numerical-tool accuracy.

Follow [the manual checklist](docs/phase-1-checklist.md) in a real browser as well.
Passing AppTest does not prove mobile layout, visual styling or browser downloads.

## Git and GitHub

Initialize Git if this project does not already have a repository:

```powershell
git init -b main
git status --short
git check-ignore .env .streamlit/secrets.toml uploads/chapter.pdf knowledge_base/book.pdf
```

Review the files before staging. Then:

```powershell
git add .
git diff --cached --stat
git commit -m "Build Phase 1 CA AI Assistant workspace"
```

If Git asks for your identity, set your real name and a verified GitHub email (or
GitHub-provided private email) using `git config user.name` and `git config user.email`.

Create an **empty private repository** named `ca-ai-assistant` using
[GitHub's new repository page](https://github.com/new). Do not initialize it with a
README, license or .gitignore because those would create a separate first commit.
Then replace `YOUR_USERNAME` in these commands:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/ca-ai-assistant.git
git push -u origin main
```

Use Git Credential Manager's browser sign-in if prompted; never paste a token into
a remote URL. Open the repository and confirm the source is present and
`.env`, `.venv`, PDFs and student exports are absent. Only add a remote once;
use `git remote -v` to inspect an existing remote. Follow GitHub's
[existing-project guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

A GitHub remote is not created automatically by this local scaffold. Account sign-in
and repository creation remain user steps. Cloud deployment belongs to Phase 5.

## Data and security boundaries

- Chat, feedback and issue reports live only in the current Streamlit session.
  There are no accounts, database or durable chat history.
- The last 20 complete exchanges are retained; older messages and their feedback
  are dropped. Download before refreshing or closing the browser.
- Downloads are explicit local exports and can contain the questions you entered.
  No report or feedback is sent to a third party.
- Student questions are rendered as plain text. Only static application CSS/HTML
  uses `unsafe_allow_html`; documents are not parsed.
- PDF upload is disabled until a proper ingestion pipeline exists.
- Usage telemetry is disabled. CORS and XSRF protection remain enabled.
- Input length and history limits bound a session, but they are **not** production
  authentication, abuse prevention, rate limiting or multi-user cost controls.
- The app makes no model requests, so Phase 1 incurs no LLM API usage charges.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `streamlit` or `pytest` not found | Use `.\.venv\Scripts\python.exe -m ...`, and install `requirements-dev.txt` with that same interpreter. |
| `py -3.11` cannot find Python | Install Python 3.11, reopen the terminal, or check `py --list`. |
| Port 8501 is busy | Stop the other process or run `... -m streamlit run app.py --server.port 8502` and open port 8502. |
| Page does not open automatically | Headless mode is enabled; manually visit the printed localhost URL. |
| VS Code imports are underlined | Select the project's `.venv` interpreter, not the system Python. |
| Package download fails | Check connectivity/proxy settings; keep TLS verification enabled and retry the install. |
| Chat disappears after reload | This phase has session-only history; download it first. |
| Chat does not solve my question | Expected: the model is added in Phase 2. |
| PDF uploader is greyed out | Expected: document validation and retrieval arrive in Phase 3. |
| Theme menu is missing | Run from this directory with the supplied config; don't hide Streamlit's toolbar. |

## What Phase 2 will change

See [the Phase 2 design](docs/phase-2-plan.md). The interface already records a
structured study context. A server-side AI service will consume that context and
the question and return a labelled response. Phase 2 will require choosing a
provider/model, adding the SDK and server-side secrets, implementing bounded
requests and errors, and testing with mocked responses before live calls.

**Stop here after Phase 1. Proceed to Phase 2 only after the user's confirmation.**
