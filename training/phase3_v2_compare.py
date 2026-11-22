"""Diagnostic Phase 4 comparison: old generated answers vs remediated adapter.

Run only after Phase 3 v2 adapter exists. Requires a GPU for generation.
The prior Phase 4 scenarios guided remediation, so this is *not* a fresh blind benchmark.
No auto marks are assigned; a qualified reviewer must score the full responses.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SYSTEM = (
    'You are an English-language CA study tutor. '
    'For numerical questions, show calculations, working notes, and journal entries '
    'where required. For theory, provide a structured exam-style answer. '
    'State assumptions clearly.'
)

FIELDS = (
    'question_no', 'subject', 'topic', 'marks', 'question', 'reference_answer',
    'base_answer', 'phase3_answer', 'phase3_v2_answer',
    'potential_issues_for_review', 'phase3_score', 'phase3_v2_score',
    'calculations_verified', 'journal_entries_verified',
    'audit_relevance_verified', 'answer_complete', 'reviewer', 'notes',
)


def create_review_rows(records, find_flags):
    review = []
    for idx, record in enumerate(records, 1):
        question = str(record.get('question', ''))
        old = str(record.get('phase3_answer', ''))
        new = str(record.get('phase3_v2_answer', ''))
        review.append({
            **{name: record.get(name, '') for name in FIELDS},
            'question_no': idx,
            'potential_issues_for_review': (
                'Prior: ' + '; '.join(find_flags(question, old)) + '\n'
                'New: ' + '; '.join(find_flags(question, new))
            ).strip(),
            **{key: '' for key in (
                'phase3_score', 'phase3_v2_score', 'calculations_verified',
                'journal_entries_verified', 'audit_relevance_verified',
                'answer_complete', 'reviewer', 'notes',
            )},
        })
    return review


def run(source: Path, adapter_path: Path, output: Path, max_new_tokens: int):
    if max_new_tokens < 200 or max_new_tokens > 1500:
        raise ValueError('max_new_tokens must be 200..1500')
    if not (adapter_path / 'adapter_config.json').is_file():
        raise FileNotFoundError(f'Adapter not found: {adapter_path}')
    data = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(data, list) or not data:
        raise ValueError('Expected the original Phase 4 comparison.json as a nonempty list')
    if not all(isinstance(r, dict) and r.get('question') for r in data):
        raise ValueError('Invalid Phase 4 comparison rows')
    output.mkdir(parents=True, exist_ok=True)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from .phase4_flagged_review import find_flags

    if not torch.cuda.is_available():
        raise RuntimeError('Enable a T4 GPU in Colab')
    model_id = 'Qwen/Qwen2.5-1.5B-Instruct'
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    base = AutoModelForCausalLM.from_pretrained(
        model_id, device_map={'': 0}, quantization_config=config, dtype=torch.float16
    )
    model = PeftModel.from_pretrained(base, str(adapter_path))
    model.eval()
    model.config.use_cache = True

    partial = output / 'phase3_v2_partial.json'
    saved = json.loads(partial.read_text(encoding='utf-8')) if partial.exists() else {}
    if not isinstance(saved, dict):
        saved = {}
    results = []
    for idx, item in enumerate(data, 1):
        question = item['question']
        print(f'Evaluating {idx}/{len(data)}: {item.get("topic", "unknown")}')
        key = str(idx) + ':' + question
        if key in saved:
            answer = saved[key]
        else:
            prompt = tokenizer.apply_chat_template(
                [{'role':'system','content':SYSTEM}, {'role':'user','content':question}],
                tokenize=False, add_generation_prompt=True,
            )
            encoded = tokenizer(prompt, return_tensors='pt', add_special_tokens=False)
            encoded = {k: v.to('cuda') for k, v in encoded.items()}
            length = encoded['input_ids'].shape[1]
            with torch.inference_mode():
                prediction = model.generate(
                    **encoded, do_sample=False, max_new_tokens=max_new_tokens,
                    pad_token_id=tokenizer.eos_token_id,
                )
            answer = tokenizer.decode(prediction[0, length:], skip_special_tokens=True).strip()
            saved[key] = answer
            partial.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding='utf-8')
        results.append({**item, 'phase3_v2_answer': answer})

    (output / 'comparison_v2.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    rows = create_review_rows(results, find_flags)
    with (output / 'review_v2.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(f'Comparison completed: {len(results)} cases. No automatic examination marks were assigned.')
    print('Before/after:', output / 'comparison_v2.json')
    print('Human review:', output / 'review_v2.csv')
    print('IMPORTANT: Old Phase 4 cases were seen during remediation; evaluate independent cases before release.')
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True, help='Original Phase 4 comparison.json')
    p.add_argument('--adapter', type=Path, required=True, help='Phase 3 v2 LoRA adapter directory')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-new-tokens', type=int, default=850)
    args = p.parse_args()
    run(args.input, args.adapter, args.output, args.max_new_tokens)


if __name__ == '__main__':
    main()
