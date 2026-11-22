"""Experimental CA-style QLoRA pilot on an NVIDIA Colab T4.

Input is generated original practice, not official ICAI training data.
The 48 held-out records are never included in the training set. This command
runs only after explicit --experimental acceptance: it is not production safe.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def validate(path: Path):
    manifest = json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    train_text = (path/'train_sft.jsonl').read_bytes()
    if hashlib.sha256(train_text).hexdigest() != manifest['sha256_train']:
        raise ValueError('Train file hash differs from manifest. Rebuild the dataset.')
    train_rows = read_jsonl(path/'train_records.jsonl')
    eval_rows = read_jsonl(path/'eval_records.jsonl')
    train_sft = read_jsonl(path/'train_sft.jsonl')
    eval_sft = read_jsonl(path/'eval_sft.jsonl')
    if not train_rows or not eval_rows or len(train_rows) != len(train_sft) or len(eval_rows) != len(eval_sft):
        raise ValueError('Input split files are missing or inconsistent')
    train_families = {row['scenario_family'] for row in train_rows}
    eval_families = {row['scenario_family'] for row in eval_rows}
    if train_families & eval_families:
        raise ValueError('Scenario family leakage between training and evaluation')
    if any(x['human_reviewed'] for x in train_rows):
        raise ValueError('Generated examples should not be marked human-reviewed automatically')
    return manifest, train_sft, eval_sft


def run(data: Path, output: Path, prior_adapter: Path | None, steps: int, max_length: int):
    import torch
    from datasets import Dataset
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTConfig, SFTTrainer

    manifest, train_rows, eval_rows = validate(data)
    if not torch.cuda.is_available():
        raise RuntimeError('Please select a GPU in Colab: Runtime → Change runtime type → T4 GPU')
    print('GPU:', torch.cuda.get_device_name(0))
    print('Train questions:', len(train_rows), 'Held-out:', len(eval_rows))
    print('Assessment families withheld:', ', '.join(manifest['held_out_families']))
    if steps < 1 or steps > 500 or not (400 <= max_length <= 2048):
        raise ValueError('steps must be 1..500; max_length must be 400..2048')
    output.mkdir(parents=True, exist_ok=True)
    base_id = 'Qwen/Qwen2.5-1.5B-Instruct'
    tokenizer = AutoTokenizer.from_pretrained(base_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
    base = AutoModelForCausalLM.from_pretrained(base_id, quantization_config=config,
                                                device_map={'': 0}, dtype=torch.float16)
    base.config.use_cache = False
    base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
    if prior_adapter is not None:
        if not (prior_adapter/'adapter_config.json').exists():
            raise FileNotFoundError(f'Previous adapter not found: {prior_adapter}')
        model = PeftModel.from_pretrained(base, str(prior_adapter), is_trainable=True)
        print('Continuing from saved pilot adapter:', prior_adapter)
    else:
        model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                                               target_modules=['q_proj','v_proj'], task_type='CAUSAL_LM'))
    for param in model.parameters():
        if param.requires_grad and param.dtype != torch.float32:
            param.data = param.data.float()
    dtypes = Counter(str(p.dtype) for p in model.parameters() if p.requires_grad)
    if set(dtypes) != {'torch.float32'}:
        raise RuntimeError('Expected all trainable LoRA parameters in FP32: '+str(dtypes))
    checkpoint_dir = output/'checkpoints'
    args = SFTConfig(output_dir=str(checkpoint_dir), per_device_train_batch_size=1,
                     per_device_eval_batch_size=1, gradient_accumulation_steps=4,
                     learning_rate=1e-4, max_steps=steps, max_length=max_length,
                     fp16=False, bf16=False, optim='adamw_torch',
                     completion_only_loss=True, eos_token='<|im_end|>',
                     packing=False, logging_steps=10, save_strategy='steps', save_steps=15,
                     save_total_limit=2, report_to='none', seed=42)
    trainer = SFTTrainer(model=model, args=args, train_dataset=Dataset.from_list(train_rows),
                         eval_dataset=Dataset.from_list(eval_rows), processing_class=tokenizer)
    checkpoints = sorted(checkpoint_dir.glob('checkpoint-*'),
                         key=lambda p: int(p.name.rsplit('-',1)[-1])) if checkpoint_dir.exists() else []
    resume = str(checkpoints[-1]) if checkpoints else None
    print('Checkpoint:',resume or 'new run')
    result = trainer.train(resume_from_checkpoint=resume)
    adapter = output/'adapter'
    adapter.mkdir(exist_ok=True)
    trainer.model.save_pretrained(str(adapter))
    tokenizer.save_pretrained(str(adapter))
    print('Trained adapter saved:', adapter)
    try:
        metrics = trainer.evaluate()
        print('Held-out completion loss:', metrics.get('eval_loss'))
    except Exception as exc:
        metrics = {'evaluation_error': type(exc).__name__}
        print('Evaluation exception:', type(exc).__name__)
    # Generate a small qualitative sample only; never judge correctness by loss alone.
    model = trainer.model
    model.eval()
    model.config.use_cache = True
    samples = []
    for row in eval_rows[:4]:
        messages = row['prompt']
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, add_special_tokens=False, return_tensors='pt')
        inputs = {k:v.to('cuda') for k,v in inputs.items()}
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=480, do_sample=False,
                                       pad_token_id=tokenizer.eos_token_id)
        answer = tokenizer.decode(generated[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        samples.append({'question': messages[-1]['content'], 'reference_answer': row['completion'][0]['content'],
                        'generated_answer': answer, 'correctness_reviewed': False})
    summary = {'base_model': base_id, 'prior_adapter': str(prior_adapter) if prior_adapter else None,
               'adapter': str(adapter), 'train_examples':len(train_rows), 'held_out_examples':len(eval_rows),
               'train_scenario_families': manifest['train_families'],
               'held_out_scenario_families':manifest['held_out_families'],
               'steps': steps, 'max_length': max_length, 'train_loss': result.training_loss,
               'eval_metrics': metrics, 'generation_samples': samples,
               'icai_exam_accuracy_verified':False, 'human_review_completed':False,
               'production_ready':False}
    (output/'results.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print('PHASE 3 PILOT TRAINING AND EVALUATION COMPLETE')
    print('Report:', output/'results.json')
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=Path('data/training/phase3'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--from-adapter', type=Path)
    p.add_argument('--steps',type=int, default=48)
    p.add_argument('--max-length',type=int,default=896)
    p.add_argument('--experimental', action='store_true', help='Acknowledge original generated data are not human-reviewed')
    args = p.parse_args()
    if not args.experimental:
        p.error('--experimental is required because this dataset is not human-reviewed or exam-verified')
    run(args.data, args.output, args.from_adapter, args.steps, args.max_length)


if __name__ == '__main__':
    main()

