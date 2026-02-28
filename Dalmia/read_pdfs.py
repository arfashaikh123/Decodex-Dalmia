import PyPDF2, os

base = r'c:\Users\mansu\Downloads\02 – Case GRIDSHIELD'
for fname in ['Case 02 - Stage Guidelines.pdf', 'Finale Round Guidelines .pdf', 'Hackathon Case 2 Roadmap Development.pdf']:
    fpath = os.path.join(base, fname)
    if os.path.exists(fpath):
        reader = PyPDF2.PdfReader(fpath)
        print(f'\n===== {fname} ({len(reader.pages)} pages) =====')
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                print(f'--- Page {i+1} ---')
                print(text[:5000])
    else:
        print(f'NOT FOUND: {fname}')
