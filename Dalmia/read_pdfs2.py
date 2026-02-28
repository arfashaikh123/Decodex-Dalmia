import PyPDF2, os

base = r'c:\Users\mansu\Downloads\02 – Case GRIDSHIELD'
for fname in ['Case 02 - Stage Guidelines.pdf', 'Finale Round Guidelines .pdf', 'Hackathon Case 2 Roadmap Development.pdf']:
    fpath = os.path.join(base, fname)
    if os.path.exists(fpath):
        reader = PyPDF2.PdfReader(fpath)
        print(f'\n{"="*80}')
        print(f'FILE: {fname} ({len(reader.pages)} pages)')
        print(f'{"="*80}')
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f'\n--- Page {i+1} ---\n{text}\n'
        print(full_text)
    else:
        print(f'NOT FOUND: {fname}')
