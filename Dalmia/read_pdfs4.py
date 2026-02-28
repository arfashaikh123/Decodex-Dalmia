import PyPDF2, os

base = r'c:\Users\mansu\Downloads\02 – Case GRIDSHIELD'
output_file = os.path.join(base, 'pdf_contents.txt')

with open(output_file, 'w', encoding='utf-8') as out:
    for fname in ['Case 02 - Stage Guidelines.pdf', 'Finale Round Guidelines .pdf', 'Hackathon Case 2 Roadmap Development.pdf']:
        fpath = os.path.join(base, fname)
        if os.path.exists(fpath):
            reader = PyPDF2.PdfReader(fpath)
            out.write(f'\n{"="*80}\n')
            out.write(f'FILE: {fname} ({len(reader.pages)} pages)\n')
            out.write(f'{"="*80}\n')
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    out.write(f'\n--- Page {i+1} ---\n')
                    out.write(text + '\n')
        else:
            out.write(f'NOT FOUND: {fname}\n')

print(f"Written to {output_file}")
