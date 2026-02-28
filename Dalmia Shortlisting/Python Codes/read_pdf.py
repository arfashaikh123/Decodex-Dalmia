import pypdf
import sys

try:
    reader = pypdf.PdfReader("d:/ARFA PROJECTS/Decodex Dalmia/DecodeX - Case study overview.docx.pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    with open("case_study_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("PDF text extracted successfully.")
except Exception as e:
    print(f"Error reading PDF: {e}")
