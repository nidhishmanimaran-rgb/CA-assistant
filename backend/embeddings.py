"""Local lexical baseline and real provider embeddings; modes are never conflated."""
import hashlib
import math
import re
from backend.errors import AppError


class LocalEmbeddings:
    identifier = "local-keyword-sha256-v1:512"
    semantic = False
    dimensions = 512

    def encode(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"\w+", text.casefold()):
                if len(token) < 2 or token in {"the", "and", "for", "with", "what", "that", "this", "are", "from"}:
                    continue
                index = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % self.dimensions
                vector[index] += 1
            norm = math.sqrt(sum(value * value for value in vector)) or 1
            vectors.append([value / norm for value in vector])
        return vectors


class OpenAIEmbeddings:
    semantic = True

    def __init__(self, provider):
        self.provider = provider
        self.identifier = "openai:" + provider.settings.embedding_model

    def encode(self, texts):
        if not texts:
            return []
        vectors = []
        for offset in range(0, len(texts), 32):
            vectors.extend(self.provider.embed(texts[offset:offset + 32]))
        return vectors


def validate_vectors(vectors, count):
    if len(vectors) != count or not vectors:
        raise AppError("The embedding service returned an invalid vector count.", "embedding")
    dimension = len(vectors[0])
    if not 1 <= dimension <= 4096:
        raise AppError("Unsupported embedding dimension.", "embedding")
    for vector in vectors:
        if len(vector) != dimension or any(not math.isfinite(float(value)) for value in vector):
            raise AppError("Invalid embedding values.", "embedding")
    return vectors
