# Model customization

training/ contains licensed-data preparation and Google Vertex supervised-tuning submission utilities. They validate rights, human review, identifiers, leakage-resistant scenario-family splits, and immutable hashes.

    python -m training.prepare --input reviewed.jsonl --output data/training --licensed --human-reviewed --reviewer reviewer-id
    python -m training.run status --config training/config.example.json

Submission needs Google credentials, project/GCS URIs, at least 100 reviewed examples, current price/token estimates, and an explicit budget. No cloud job, checkpoint, or tuned model was created. The main application remains OpenAI/RAG based; Vertex is an optional separate deployment. OpenAI fine-tuning was not run.
