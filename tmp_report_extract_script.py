from pypdf import PdfReader
from pathlib import Path
pdf = Path(r"C:\Users\aitlh\Downloads\main (39).pdf")
out = Path(r"D:\github\Master_PFE_Project\tmp_report_extract")
out.mkdir(exist_ok=True)
reader = PdfReader(str(pdf))
all_text = []
for i, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    (out / f"page_{i:03d}.txt").write_text(text, encoding="utf-8")
    all_text.append(f"===== PAGE {i} =====\n{text}\n")
(out / "all_pages.txt").write_text("\n".join(all_text), encoding="utf-8")
print(len(reader.pages))
