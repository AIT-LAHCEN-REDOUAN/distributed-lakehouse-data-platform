import os
pdf = r"D:\github\Master_PFE_Project\CustomerDNA AI\project_presentation\PFE_report\main.pdf"
out = r"D:\github\Master_PFE_Project\CustomerDNA AI\project_presentation\PFE_report\_preview_ch2"
os.makedirs(out, exist_ok=True)
try:
    import fitz
    doc = fitz.open(pdf)
    for p in [18,19,20,21]:
        page = doc[p-1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2), alpha=False)
        pix.save(os.path.join(out, f"page_{p}.png"))
    print('fitz ok')
except Exception as e:
    print('fitz failed', e)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf)
    for p in [18,19,20,21]:
        page = doc[p-1]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        pil_image.save(os.path.join(out, f"page_{p}.png"))
    print('pdfium ok')
print('\n'.join(sorted(os.listdir(out))))
