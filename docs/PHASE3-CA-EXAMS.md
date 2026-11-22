# Phase 3: original CA-style full-solution training pilot

**Aim:** Extend the successful formula-only QLoRA adapter toward structured, longer **10-mark and 16-mark practice responses**. This is not official ICAI course material or an assertion of mark-scheme alignment.

## What's generated

Run from the repo root:

```bash
python -m training.ca_exam_phase3 --out data/training/phase3 --train-per-family 36 --eval-per-family 12
```

Outputs (all under ignored `data/`, not GitHub):

- `train_records.jsonl` and `train_sft.jsonl` (144 original samples, 72 accounting / 36 costing / 36 finance)
- `eval_records.jsonl` and `eval_sft.jsonl` (48 samples; **entirely different question scenario families**)
- `review_sheet.csv` (manual subject review; entries not pre-approved)
- `manifest.json` (dataset counts, fingerprints, and restrictions)

The **training families** are PPE depreciation schedules with journal entries, CVP calculations, NPV and SLM-versus-WDV theory. The **held-out assessment families** are PPE disposal journal entries, material variances, WACC and audit evidence theory. Deliberately withheld topic families provide a harder test than random number variants of the same template.

Every exercise and solution is original/generated in this repo. Arithmetic is derived and verified in Python for the numerical families. **Exam validity, applicable CA standards, expected mark allocations, and theory details still require qualified human review.** No external FinQA/TAT-QA/FinanceMath/BhashaBench/IndFin content is used by this Phase 3 generator.

## Colab experiment (separate from production)

With a T4 enabled and Drive mounted, install the same training dependencies previously used (or reuse the existing Colab session). After creating the Phase 3 files, run:

```bash
python -m training.phase3_train \
  --data data/training/phase3 \
  --output /content/drive/MyDrive/CA-AI-Assistant/models/phase3-exam \
  --from-adapter /content/drive/MyDrive/CA-AI-Assistant/models/unified-runs/cce5af2dd47c/adapter \
  --steps 48 --max-length 896 --experimental
```

Use `--experimental` only to explicitly acknowledge that the original synthetic examples are **machine-generated, not human-reviewed**. Remove `--from-adapter` to train a separate new adapter from the base model instead. The script uses 4-bit QLoRA, FP32 trainable LoRA parameters and no AMP scaler (avoids the previous BF16-grad error), saves 15-step checkpoints, and evaluates against the held-out family split.

A `results.json` records held-out loss and a few qualitative generations. Evaluation loss is **not a CA exam score**. Before considering public use, manually review the `review_sheet.csv`, verify solutions and applicable standards, assess longer answers with a qualified reviewer, and test real licensed questions with a separately sourced benchmark.

## Deployment status

Streamlit is unchanged by Phase 3; the trained adapter is saved on private Drive, **not served to the public website**. A persistent model inference service and provider adapter are needed for deployment. Do not publish benchmark data, study PDFs, Drive shares, or Hugging Face tokens on GitHub.