"""Broad navigation catalogue, not an authoritative or attempt-verified syllabus."""

APP_TITLE = "CA AI Assistant"
MVP_CHAPTER = "Property, plant and equipment — depreciation"

CATALOG = {
    "CA Foundation": {
        "Accounting": ("Accounting principles", "Journal and ledger", "Final accounts"),
        "Business Laws": ("Contract law", "Sale of goods", "Company basics"),
        "Quantitative Aptitude": ("Business mathematics", "Logical reasoning", "Statistics"),
        "Business Economics": ("Demand and supply", "Market structures", "National income"),
    },
    "CA Intermediate": {
        "Advanced Accounting": (
            MVP_CHAPTER, "Accounting standards — overview",
            "Amalgamation of companies", "Consolidated financial statements",
        ),
        "Corporate and Other Laws": ("Company law", "Other laws", "Contract fundamentals"),
        "Taxation": ("Income-tax overview", "Goods and Services Tax", "Applicability and amendments"),
        "Cost and Management Accounting": ("Cost concepts", "Marginal costing", "Budgeting", "Standard costing"),
        "Auditing and Ethics": ("Audit planning", "Audit evidence", "Professional ethics"),
        "Financial Management": ("Time value of money", "Capital budgeting", "Working capital", "Cost of capital"),
        "Strategic Management": ("SWOT and PESTLE", "Competitive strategy", "Portfolio analysis"),
    },
    "CA Final": {
        "Financial Reporting": ("Financial reporting concepts", "Accounting standards"),
        "Advanced Financial Management": ("Risk management", "Capital investment decisions"),
        "Advanced Auditing, Assurance and Professional Ethics": ("Auditing standards", "Ethical requirements"),
        "Direct Tax Laws and International Taxation": ("Direct tax principles", "International taxation"),
        "Indirect Tax Laws": ("GST concepts", "Customs concepts"),
        "Integrated Business Solutions": ("Integrated case analysis", "Strategic decision-making"),
    },
}

ANSWER_FORMATS = (
    "Simple explanation",
    "Detailed solution",
    "Examination-style answer",
)
MAX_QUESTION_CHARS = 4000
MAX_TURNS = 20
