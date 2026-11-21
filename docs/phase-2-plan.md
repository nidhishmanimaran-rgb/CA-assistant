# Phase 2 plan — no provider integration implemented yet

## Connection point

The current flow is:

```text
Student question + StudyContext
    -> backend.demo.build_demo_response()
    -> session record
    -> Streamlit chat display
```

Phase 2 will replace the demo service for actual questions with a server-side
`backend/ai_engine.py` provider adapter. Keep the prepared layout example explicitly
separate. The adapter will accept the question, bounded conversation context,
CA level, subject, chapter, attempt label, language and requested answer format.

## Work after confirmation

1. Select OpenAI or Gemini and an available model using current provider documentation,
   cost and privacy constraints. Do not choose or bill a model silently.
2. Install only the selected provider's supported SDK and add validated server-side
   configuration. Read local environment variables (with an explicit .env loader)
   or cloud secrets later; never expose keys in browser code.
3. Add clear system instructions for uncertainty, missing facts, unsupported subjects,
   and non-official educational explanations. Preserve the distinction between
   conceptual help, calculation and legal interpretation.
4. Bound the message history, input size, output tokens, timeout and retry count.
   Handle missing keys, invalid credentials, rate limits and provider outages without
   showing secrets or logging full student prompts.
5. Add an explicit model/source status to replies. Before Phase 3 there is no document
   grounding: do not fabricate page references or claim verified attempt applicability.
   Before Phase 4 there is no independently validated numerical calculation layer.
6. Test request construction and failures with a mock provider. Make a small live
   smoke test only once a provider and key are configured, reporting what was tested.

No real API key is needed in conversation. Configure it locally when this phase is
approved. Using a pretrained model is inference; indexing documents is RAG, not
training. Fine-tuning changes a model using examples and remains optional in Phase 7.
Continued pretraining uses additional domain text; training from scratch creates a
new foundation model. Neither is part of this MVP.
