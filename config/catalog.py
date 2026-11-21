"""A small UI catalogue, not an authoritative or attempt-verified syllabus."""

APP_TITLE = "CA AI Assistant"
MVP_CHAPTER = "Property, plant and equipment — depreciation"

CATALOG = {
    "CA Foundation": {
        "Accounting": ("Course preview — available in a later phase",),
    },
    "CA Intermediate": {
        "Advanced Accounting": (
            MVP_CHAPTER,
            "Accounting standards — overview",
            "Amalgamation of companies",
            "Consolidated financial statements",
        ),
        "Cost and Management Accounting": ("Subject preview — available later",),
        "Financial Management": ("Subject preview — available later",),
        "Taxation": ("Subject preview — available later",),
    },
    "CA Final": {
        "Financial Reporting": ("Course preview — available in a later phase",),
    },
}

ANSWER_FORMATS = (
    "Simple explanation",
    "Detailed solution",
    "Examination-style answer",
)
MAX_QUESTION_CHARS = 4000
MAX_TURNS = 20
