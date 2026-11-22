"""Generate original, redistributable sample material. No copied textbooks."""
from pathlib import Path
from reportlab.pdfgen import canvas

TEXT = [
    "CA AI Assistant: original depreciation practice notes (CC0-1.0)",
    "Residual value is the estimated amount recoverable at the end of useful life,",
    "after expected disposal costs. Review estimates and applicable accounting rules.",
    "Straight-line depreciation allocates cost less residual value over useful life.",
    "Example: cost INR 850000, residual INR 50000, useful life 8 years.",
    "Annual charge for a full year = (850000 - 50000) / 8 = INR 100000.",
    "For six months under an agreed monthly convention: INR 50000.",
    "This original educational note is not an official ICAI publication.",
]

if __name__=="__main__":
    target=Path("data/sample-depreciation.pdf")
    target.parent.mkdir(parents=True,exist_ok=True)
    document=canvas.Canvas(str(target))
    text=document.beginText(45,780)
    for line in TEXT:
        text.textLine(line)
    document.drawText(text)
    document.save()
    print(target.resolve())
