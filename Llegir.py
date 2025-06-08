import fitz  # PyMuPDF

INPUT_FILE = "Input/ejemplo.pdf"
OUTPUT_FILE = "Output/ejemplo.txt"

with fitz.open(INPUT_FILE) as doc:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for page in doc:
            text = page.get_text()
            f.write(text)
            f.write("\n" + "="*80 + "\n")  # separador entre pàgines opcional

print(f"✅ Text extret i guardat a: {OUTPUT_FILE}")
