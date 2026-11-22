# Phase 3 v2 — Targeted remediation and review

**Status: experimental, not production or official ICAI study material.** This change responds to known weaknesses in a Phase 4 comparison, especially an answer about trade receivables that misdefined sufficiency and introduced irrelevant auditing procedures. We have **not reviewed every response in the user's private `comparison.json`**; that file remains in their Google Drive and must be reviewed separately.

## Improvements

1. Generate **144 new original training examples** across trade-receivables audit evidence, machinery-disposal journal entries, material price/usage variances, and after-tax market-value WACC. Both 10-mark and 16-mark formats are generated.
2. Generate **32 new variant evaluation problems** (8 per topic). The parameterized cases are not duplicated in training, but evaluation topics overlap with training and are therefore **not an independent curriculum/generalization benchmark**. The previous Phase 4 questions should be treated as diagnostic cases once these concepts have been fine-tuned.
3. Add Python assertions for disposal journal debit/credit totals, variance reconciliation, and weight/formula checks. Arithmetic checking is not human subject-matter validation.
4. Improve audit-answer targets to define sufficiency as quantity and appropriateness as relevance and reliability, link procedures to relevant receivables assertions, and avoid padding with unrelated procedures. These are original paraphrases consistent with ICAI SA 500/SA 505, not reproduced ICAI text. Official reference: [ICAI Standards on Auditing](https://www.icai.org/post/auditing-review-and-other-standards-formerly-known-as-aas-complete-text).
5. Produce **private, blank human-review sheets**. The `phase4_flagged_review.py` script inspects the user's private `comparison.json` and flags potentially irrelevant wording; it does **not** assign accuracy scores.

## Generate and test locally

```bash
python -m training.phase3_v2 --out data/training/phase3-v2 \
  --train-per-family 36 --eval-per-family 8
pytest -q tests/test_phase3_v2.py
```

Outputs `train_records.jsonl`, `train_sft.jsonl`, `eval_records.jsonl`, `eval_sft.jsonl`, `manifest.json` and `review_sheet.csv` under ignored local `data/`.

## Optional pilot on Colab T4

After fetching the branch and generating the dataset, continue from the **previous Phase 3 adapter**, not from the original Phase 2 adapter:

```bash
python -m training.phase3_train \
  --data data/training/phase3-v2 \
  --output /content/drive/MyDrive/CA-AI-Assistant/models/phase3-v2 \
  --from-adapter /content/drive/MyDrive/CA-AI-Assistant/models/phase3-exam/adapter \
  --steps 48 --max-length 896 --experimental
```

The reused trainer already uses 4-bit QLoRA, trainable FP32 LoRA weights and `fp16=False`, `bf16=False`, avoiding the specific BF16 unscale failure on the user's T4. It saves checkpoints and the adapter to Drive and generates a few qualitative samples. The results require **human accuracy review**, even when validation loss declines.

Build an issues worksheet for the *original* Phase 4 comparison:

```bash
python -m training.phase4_flagged_review \
  --input /content/drive/MyDrive/CA-AI-Assistant/models/phase4-evaluation/comparison.json \
  --output /content/drive/MyDrive/CA-AI-Assistant/models/phase4-evaluation/flagged_review.csv
```

Keep the original `comparison.json`, Phase 3 adapter, and original generated dataset intact. **Do not upload private Drive data or trained weights to public GitHub.** No model is deployed to Streamlit by this pull request. Training on generated, unreviewed examples remains a controlled experiment.

## Before/after Phase 4 diagnostic (same questions)

After the v2 adapter is saved, compare against the **existing eight Phase 4 questions** (new model generations only; prior answers are read from the saved JSON):

```bash
python -m training.phase3_v2_compare \
  --input /content/drive/MyDrive/CA-AI-Assistant/models/phase4-evaluation/comparison.json \
  --adapter /content/drive/MyDrive/CA-AI-Assistant/models/phase3-v2/adapter \
  --output /content/drive/MyDrive/CA-AI-Assistant/models/phase4-evaluation/v2 \
  --max-new-tokens 850
```

This writes `comparison_v2.json` plus an **unscored** `review_v2.csv`, with resumption after interrupted generations. Compare the original Phase 3 answers to the new Phase 3 v2 answers by hand. These eight questions **are not independent after targeted remediation**, because the earlier audit error and the four evaluated subjects motivated the new training. Use the 32 new parameterized cases only as a smoke test; before production, design a separate, unseen, expert-marked benchmark across distinct topics and difficulty levels.
