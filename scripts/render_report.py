"""Render every report page for visual QA; install requirements-dev.txt."""
from pathlib import Path
import pymupdf

root=Path(__file__).resolve().parents[1]
out=root/'tmp'/'pdfs';out.mkdir(parents=True,exist_ok=True)
document=pymupdf.open(root/'output'/'pdf'/'PathSnap_Technical_Report.pdf')
for i,page in enumerate(document):
    page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(out/f'page_{i+1:02d}.png')
print(f'Rendered {len(document)} pages to {out}')
