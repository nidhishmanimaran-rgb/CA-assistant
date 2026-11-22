"""Human-review worksheet for the user's *existing* Phase 4 comparison JSON.

Simple patterns flag potential problems; they do not assign examination marks.
Never treat a pattern match as proof of factual error.
"""
import argparse
import csv
import json
from pathlib import Path

AUDIT_REVIEW_PHRASES = {
    'physical inventory': 'Confirm this procedure relates to receivables, not inventory.',
    'vendor statements': 'Vendor statements generally relate to payables; check relevance.',
    'bank statement balance': 'Bank balance comparisons do not directly confirm receivables.',
    'external audits': 'Calling another external audit is not a specific receivables test.',
    'management interviews': 'Management inquiry requires appropriate corroboration.',
    'management explanations': 'Management inquiry requires appropriate corroboration.',
    'reduces the tax liability': 'This claim depends on applicable law and facts.',
}


def find_flags(question: str, answer: str):
    q, a = question.lower(), answer.lower()
    flags = []
    if 'receivable' in q or 'audit evidence' in q:
        if 'sufficien' in a and 'quantity' not in a:
            flags.append('Sufficiency should be defined as evidence quantity.')
        if 'appropriateness' in a and not all(v in a for v in ('relevan', 'reliab')):
            flags.append('Appropriateness should address relevance and reliability.')
        if ('adequate internal controls' in a or 'effective internal controls' in a) and not ('control' in q and ('tested' in q or 'effective' in q)):
            flags.append('Unverified assumption about effective internal controls.')
        if ('low-quality evidence may still be sufficient' in a or 'poor-quality evidence can be sufficient' in a):
            flags.append('Weak-quality evidence is not necessarily remedied by quantity.')
        for phrase, message in AUDIT_REVIEW_PHRASES.items():
            if phrase in a:
                flags.append(f'Inspect: {message}')
    return list(dict.fromkeys(flags))


def make_review(source: Path, output: Path):
    records = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(records, list):
        raise ValueError('Expected Phase 4 comparison.json containing a list')
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ['question_no', 'subject', 'topic', 'marks', 'question',
              'reference_answer', 'base_answer', 'phase3_answer',
              'potential_issues_for_review', 'base_score', 'phase3_score',
              'numerical_result_verified', 'journal_entries_balanced',
              'relevance_verified', 'completeness_verified', 'reviewer', 'notes']
    with output.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for i, record in enumerate(records, 1):
            q = record.get('question', '')
            a = record.get('phase3_answer', '')
            writer.writerow({
                **{k: record.get(k, '') for k in fields},
                'question_no': i,
                'potential_issues_for_review': ' | '.join(find_flags(q, a)),
                'base_score': '', 'phase3_score': '',
                'numerical_result_verified': '', 'journal_entries_balanced': '',
                'relevance_verified': '', 'completeness_verified': '',
                'reviewer': '', 'notes': ''
            })
    return len(records)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    count = make_review(args.input, args.output)
    print(f'Created human review for {count} model comparisons: {args.output}')
    print('Potential issues flagged; no automatic exam marks assigned.')


if __name__ == '__main__':
    main()
