"""Read-only dataset registry and locally uploaded metadata overview."""
import json

import streamlit as st

from training.unified_datasets import SOURCES, public_manifest


def render_dataset_status() -> None:
    st.subheader("CA training datasets — English")
    st.write(
        "This page tracks dataset sources for the Colab workflow. "
        "The datasets are not bundled with Streamlit or automatically approved for training."
    )
    st.info(
        "FinQA and TAT-QA are review candidates. FinanceMath, BhashaBench-Finance "
        "and IndFin-Bench are reserved for independent evaluation. "
        "Public availability does not grant unrestricted model-training rights."
    )
    st.dataframe(
        [{"Dataset": s.title, "Use": s.role.replace("_", " "),
          "Access": s.access, "Rights": s.license_note, "Link": s.url}
         for s in SOURCES],
        hide_index=True,
        use_container_width=True,
    )
    uploaded = st.file_uploader(
        "Optional: upload Colab public_manifest.json (counts only; no questions)",
        type=["json"], key="dataset_public_manifest",
        help="Upload only the sanitized public_manifest.json from Colab.",
    )
    if uploaded:
        if uploaded.size > 100_000:
            st.error("The status file exceeds the 100 KB limit.")
            return
        try:
            summary = public_manifest(json.loads(uploaded.getvalue()))
        except (ValueError, TypeError, KeyError):
            st.error("Invalid dataset status JSON.")
            return
        for source in summary["sources"]:
            st.write(
                f"{source['source']}: {source['status']} — "
                f"{source['records']} staged records"
            )
            if source["subject_distribution"]:
                st.caption(
                    ", ".join(f"{k}: {v}" for k, v in
                              source["subject_distribution"].items())
                )
        st.warning("Staged records are NOT verified CA training examples.")
    st.caption(
        "Colab downloads and reviews stay private. Streamlit does not train "
        "or host a GPU model. English response generation needs a configured provider."
    )
