# Student experience expansion — daily quiz and subject coverage

## Included in this proposed change
- Study-friendly, muted green hero styling and a new **Daily 20 marks** tab.
- Exactly 20 one-mark multiple-choice questions per India calendar date.
- Daily selection is stable for all students on a given date, with at least two questions from each of the seven CA Intermediate subject areas in the starter bank.
- One-question-at-a-time submission, progress meter, marks, final score and explanations.
- Expanded CA Foundation, Intermediate, and Final topic navigation.
- Offline original practice-question bank and scoring tests. No AI credentials needed to try the quiz.

## Important accuracy and privacy limits
- Questions are **original prototype study exercises**, not official ICAI material or a verified 2027 question bank. A qualified subject reviewer should verify them and label each question with syllabus/exam-attempt applicability before public exam-preparation claims.
- Subject menus are navigation topics, not evidence that each subject has been independently trained and validated.
- Daily progress is in Streamlit session state, not an authenticated database. Refresh, restarts, and server rescheduling can lose progress. Implement login and persistent per-user results for daily streaks and multi-device continuity.
- The same starter pool will recur. Publish more reviewed, licensed questions before using the quiz for prolonged daily study.
- This update does **not** start cloud fine-tuning, authorize paid API requests, or replace the current retrieval/evaluation workflow.

## Optional cloud training — prerequisites
1. Select an actual supported base model/provider, supported tuning method and region, confirmed against current documentation.
2. Gather permission-cleared ICAI-aligned subject data, including reviewer-approved examples, metadata and examination-attempt versions.
3. Run data sanitation, document-deduplication and train/validation/test splits; keep variant questions together to prevent leakage.
4. Establish a real-model baseline with held-out concept, calculation, source-grounding and changed-scenario evaluations.
5. Obtain authorization for training cost, credential access and retention rules. Never expose secret keys through GitHub.
6. Run a small pilot tuning job **only after** the above checks. Compare to the baseline and deploy only if demonstrated improvement.
7. Add a persistent authenticated progress store and secure multi-user document isolation before public student accounts.

The existing `training/` scripts are preparation utilities; they are not evidence that cloud training has run.
