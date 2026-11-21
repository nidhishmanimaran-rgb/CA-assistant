# Phase 1 acceptance checklist

Run from the project directory with the environment's Python.

## Automated

- [ ] `python -m pip check` reports no broken dependencies.
- [ ] `python -m pytest` passes all tests.
- [ ] No API key is needed for startup or tests.

## Browser

- [ ] `python -m streamlit run app.py` starts; localhost:8501 opens.
- [ ] The page clearly identifies Phase 1 and says AI is not connected.
- [ ] The initial context is Intermediate / Advanced Accounting / depreciation.
- [ ] Switch to Foundation and Final, then back. Subjects and chapters reset correctly.
- [ ] Enter an attempt label and change answer format.
- [ ] Send a question. It appears with a prewritten demo acknowledgement.
- [ ] Change the attempt label. Earlier messages keep their original settings.
- [ ] Preview a worked answer. The example is labelled as prepared and shows ₹1,00,000.
- [ ] Change the figures in a new question. No fixed example is passed off as a recalculated answer.
- [ ] Try all three answer formats and inspect the source/status disclosure.
- [ ] Mark a reply helpful, download the chat and inspect its JSON feedback and context.
- [ ] Clear chat. Messages and feedback disappear without resetting study choices.
- [ ] Study library displays a disabled PDF upload; it claims no indexed documents.
- [ ] Save a local issue, download it, and confirm no report was sent anywhere.
- [ ] Test the native light/dark themes and a narrow browser window.
- [ ] Check keyboard navigation and readable labels.
- [ ] Stop the server using Ctrl+C.

## GitHub (requires your account)

- [ ] Inspect `git status`; credentials, PDFs, virtual environments and exports are ignored.
- [ ] Create an empty private repository and push using the README commands.
- [ ] Check that GitHub contains the source and no private files.

## Scope check

- [ ] Confirm this is a working local UI, not a connected or production-ready AI tutor.
- [ ] Confirm that training, retrieval, calculation tools and cloud hosting are future phases.
- [ ] Approve Phase 2 before implementation begins.
