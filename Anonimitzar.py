import fitz  # PyMuPDF
import os
import re

INPUT_FILE = "Input/ejemplo.pdf"
OUTPUT_FILE = "Output/ejemplo_anon.pdf"

def extraer_datos(texto):
    datos = {}

    # Buscar tots els codis de col·legiat
    colegiados = re.findall(r'Nº Colegiado\s*:\s*([A-Za-z0-9\-]+)', texto)
    if colegiados:
        datos["Colegiados"] = []
        for colegiado in colegiados:
            colegiado = colegiado.strip()
            # Captura tota la línia després del codi
            regex = re.escape(colegiado) + r"[^\n]*"
            if m := re.search(regex, texto):
                fragment = m.group(0).strip()
                print(f"🔍 Trobat col·legiat: {fragment}")
                datos["Colegiados"].append(fragment)

    # Altres camps
    if m := re.search(r'Nombre\s*(.+)', texto):
        datos["Nombre"] = m.group(1).strip()
    if m := re.search(r'Nom del malalt\s*(.+)', texto):
        datos["Nombre"] = m.group(1).strip()
    if m := re.search(r'Nº Historia clínica\s*(.+)', texto):
        datos["Historia"] = m.group(1).strip()
    if m := re.search(r'Nº Asistencia\s*([A-Z0-9]{9})', texto):
        datos["Assistencia"] = m.group(1).strip()
    if m := re.search(r'Teléfono\s*(\d{9})', texto):
        datos["Telefono"] = m.group(1).strip()
    if m := re.search(r'C.I.P.\s*([A-Z]{4}\d{10})', texto):
        datos["CIP"] = m.group(1).strip()

    return datos

def anonimizar_pdf(input_path, output_path):
    doc = fitz.open(input_path)

    # 🟢 1. Extreure text global
    texto_global = ""
    for page in doc:
        texto_global += page.get_text()

    # 🟢 2. Detectar dades una sola vegada
    datos_encontrados = extraer_datos(texto_global)

    # 🟢 3. Aplicar redacció a cada pàgina
    for page in doc:
        for valor_completo in datos_encontrados.values():
            if isinstance(valor_completo, list):
                for valor in valor_completo:
                    rects = page.search_for(str(valor))
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
            else:
                rects = page.search_for(valor_completo)
                for rect in rects:
                    page.add_redact_annot(rect, fill=(1, 1, 1))

        # Firmes
        for text in ["Médico Responsable del Alta", "Metge/essa Responsable de l'Alta"]:
            rects = page.search_for(text)
            if rects:
                y_inicio = rects[0].y0
                zona_a_ocultar = fitz.Rect(0, y_inicio, page.rect.width, page.rect.height)
                page.add_redact_annot(zona_a_ocultar, fill=(1, 1, 1))

    for page in doc:
        page.apply_redactions()

    doc.save(output_path)
    print(f"✅ PDF anonimizado guardado en: {output_path}")

os.makedirs("Output", exist_ok=True)
anonimizar_pdf(INPUT_FILE, OUTPUT_FILE)
