# Deployment

Local launch:

    cd "C:\\Users\\ADMIN\\AI Assistant\\ca-ai-assistant"
    python -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1
    pip install -r requirements-dev.txt
    Copy-Item .env.example .env
    streamlit run app.py

The default is demo mode. Enable OpenAI only with a secret-managed key, explicit consent, ALLOW_PAID_API=true, and reviewed budget settings. Streamlit Community Cloud can host a demo, but anonymous session data and local SQLite storage are not durable production storage. Docker Compose binds to loopback, requires a password, drops Linux privileges, and uses a named data volume. Docker build was not available here.

Checks: python -m pytest -q; python -m scripts.check_release; python -m scripts.browser_smoke.

Windows Application Control blocks the FAISS native DLL on this host; retrieval automatically uses the tested pure-Python cosine fallback. Linux deployments can use pinned FAISS.
