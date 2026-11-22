# English-first Colab dataset integration

This workflow connects your **GitHub code**, a **temporary Google Colab GPU
runtime**, and a **Streamlit metadata-only status tab**. It does **not** upload
copyrighted study material, train a model automatically, or provide 24/7 GPU
inference.

## In Google Colab (English)

1. Select **Runtime > Change runtime type > T4 GPU**.
2. Create a new notebook and run the following cells in order.

```python
!git clone -b feature/colab-dataset-pipeline https://github.com/nidhishmanimaran-rgb/CA-assistant.git
%cd CA-assistant
!pip -q install datasets huggingface_hub
```

Metadata-only setup (no external downloads):

```python
!python -m training.unified_datasets --output data/datasets/unified
```

If you have checked the source terms and want to **privately stage** the two
general finance datasets for rights and answer-quality review:

```python
!python -m training.unified_datasets --sources finqa tatqa --download --limit 200
```

Optional: stage just the FinanceMath *evaluation* dataset (subject to its
dataset card and use restrictions):

```python
!python -m training.unified_datasets --sources financemath --download --limit 100
```

Gated BhashaBench requires accepting its Hugging Face terms and supplying
`HF_TOKEN` securely, **not** committing it to GitHub. IndFin-Bench requires
explicit noncommercial eligibility; by default it is excluded from downloads.
Source formats and availability can change, and unsupported records may be
skipped or the import may fail safely.

3. Inspect `data/datasets/unified/manifest.json` for source status, problems,
   and subject coverage.
4. Download **only** `data/datasets/unified/public_manifest.json` to your
   computer. In Streamlit, open **Datasets** and upload this small status file
   to view counts. The uploaded status is session-local, not permanently
   synchronized.
5. Downloaded records under `data/` are ignored by Git. Do not commit
   raw copyrighted data, tokens, checkpoints or private study documents.

### Why doesn't this directly train CA-Tutor?

Records have `approved_for_training: false`. Public QA resources do not
automatically carry permission for fine-tuning, may have third-party material,
and do not prove competence on ICAI 10-mark/16-mark questions. Review source
rights and independently verify correct answers. Build original CA-specific
training records with reviewer, licence and scenario-family metadata, use the
existing `training.prepare` validation, and hold out scenario families to
avoid question-value leakage. Then run a *separate* QLoRA training notebook.

The app's current runtime supports demo and OpenAI provider configuration;
this workflow does not yet load or serve a QLoRA adapter. The Streamlit
community-hosted instance has no persistent T4 GPU.
