"""Runtime construction and a small optional password gate."""
from collections import deque
import hashlib
import hmac
import time
from uuid import uuid4
import streamlit as st
from backend.embeddings import LocalEmbeddings, OpenAIEmbeddings
from backend.errors import AppError
from backend.providers import OpenAIProvider
from backend.retrieval import KnowledgeBase
from backend.usage import UsageLedger
from config.settings import load_settings


@st.cache_resource
def ledger():
    return UsageLedger()


def settings():
    try:
        secrets = dict(st.secrets)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        secrets = {}
    return load_settings(secrets=secrets)


def access_gate(configuration):
    if not configuration.require_password:
        return
    fingerprint = hashlib.sha256(configuration.app_password.encode()).hexdigest()
    if st.session_state.get("_authenticated") == fingerprint:
        return
    st.title("CA AI Assistant")
    st.write("Enter the workspace password to continue.")
    attempts = st.session_state.setdefault("_login_attempts", [])
    attempts[:] = [item for item in attempts if item > time.time() - 60]
    with st.form("login"):
        password = st.text_input("Workspace password", type="password")
        submitted = st.form_submit_button("Sign in", disabled=len(attempts) >= 5)
    if submitted:
        attempts.append(time.time())
        if hmac.compare_digest(password.encode(), configuration.app_password.encode()):
            st.session_state["_authenticated"] = fingerprint
            st.rerun()
        st.error("The password was not accepted.")
    if len(attempts) >= 5:
        st.warning("Too many attempts. Wait a minute and reload.")
    st.stop()


def runtime(configuration):
    workspace = st.session_state.setdefault("_workspace_id", uuid4().hex)
    provider = OpenAIProvider(configuration, ledger(), workspace) if configuration.api_enabled else None
    if configuration.embedding_backend == "openai":
        if provider is None:
            raise AppError("Semantic embeddings require enabled API access.", "configuration")
        embedder = OpenAIEmbeddings(provider)
    else:
        embedder = LocalEmbeddings()
    knowledge = KnowledgeBase(configuration.data_dir / "knowledge.sqlite", workspace, embedder)
    return provider, knowledge
