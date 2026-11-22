"""User-declared applicability. Filters never infer statutory dates or rates."""
from dataclasses import asdict, dataclass
from datetime import date
from backend.errors import AppError


def legal_subject(subject):
    return any(term in subject.casefold() for term in ("tax", "law", "gst"))


@dataclass(frozen=True)
class DocumentMeta:
    title: str
    level: str
    subject: str
    chapter: str
    attempt: str
    version: str
    publication_date: str
    topic: str = ""
    assessment_year: str = ""
    fiscal_year: str = ""
    effective_from: str = ""
    effective_to: str = ""
    timeless: bool = False

    def validate(self):
        for key in ("title", "level", "subject", "chapter", "attempt", "version", "publication_date"):
            value = getattr(self, key)
            if not isinstance(value, str) or not value.strip() or len(value) > 200:
                raise AppError(f"Provide a valid document {key}.", "metadata")
        for key in ("publication_date", "effective_from", "effective_to"):
            value = getattr(self, key)
            if value:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    raise AppError(f"{key} must be YYYY-MM-DD.", "metadata") from None
        if self.effective_to and self.effective_from > self.effective_to:
            raise AppError("Effective end date precedes the start date.", "metadata")
        if legal_subject(self.subject) and (
            self.timeless or self.attempt in ("*", "Not specified")
            or not self.effective_from or not (self.assessment_year or self.fiscal_year)
        ):
            raise AppError("Tax/law material needs an exact attempt, year and effective date; it cannot be timeless.", "metadata")
        return self

    def as_dict(self):
        return asdict(self)


def applicable(meta: DocumentMeta, context) -> bool:
    if any(getattr(meta, key) != getattr(context, key) for key in ("level", "subject", "chapter")):
        return False
    if not meta.timeless and (context.attempt == "Not specified" or meta.attempt != context.attempt):
        return False
    if legal_subject(context.subject):
        if not context.as_of or not (context.assessment_year or context.fiscal_year):
            return False
        if meta.assessment_year != context.assessment_year or meta.fiscal_year != context.fiscal_year:
            return False
        try:
            chosen = date.fromisoformat(context.as_of)
            if chosen < date.fromisoformat(meta.effective_from):
                return False
            if meta.effective_to and chosen > date.fromisoformat(meta.effective_to):
                return False
        except ValueError:
            return False
    return True
