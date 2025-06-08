import fitz  # PyMuPDF
import os
import re
import csv

INPUT_FOLDER = "C:\\FEDERAT\\INPUT_TEST"
OUTPUT_FOLDER = "C:\\FEDERAT\\OUTPUT_TEST"
CSV_LOG = os.path.join(OUTPUT_FOLDER, "Insuficiencia_pediatria_anon.csv")
os.makedirs("Output", exist_ok=True)

def extraer_datos(texto):
    datos = {}
    #Identificar idioma del informe
    idioma = "catala" if "Nom del malalt" in texto else "castella"
        
    # Buscar codigos de colegiados
    colegiados = re.findall(r'Nº Colegiado\s*:\s*([A-Za-z0-9\-]+)', texto) if idioma == "castella" else re.findall(r'Nº Col.legiat\s*:\s*([A-Za-z0-9\-]+)', texto)  
    if colegiados:
        datos["Colegiados"] = []
        for colegiado in colegiados:
            colegiado = colegiado.strip()
            # Captura toda la línea que contiene el colegiado
            regex = re.escape(colegiado) + r"[^\n]*"
            if m := re.search(regex, texto):
                fragment = m.group(0).strip()
                datos["Colegiados"].append(fragment)

    # Altres camps
    if idioma == "castella":
        if m := re.search(r'Nombre\s*(.+)', texto):
            datos["Nombre"] = m.group(1).strip()
        if m := re.search(r'Nº Historia clínica\s*(.+)', texto):
            datos["Historia"] = m.group(1).strip()
        if m := re.search(r'Nº Asistencia\s*([A-Z0-9]{9})', texto):
            datos["Assistencia"] = m.group(1).strip()
        if m := re.search(r'Teléfono\s*(\d{9})', texto):
            datos["Telefono"] = m.group(1).strip()
    else: 
        if m := re.search(r'Nom del malalt\s*(.+)', texto):
            datos["Nombre"] = m.group(1).strip()
        if m := re.search(r'Nº Història clínica\s*(.+)', texto):
            datos["Historia"] = m.group(1).strip()
        if m := re.search(r'Nº Assistència\s*([A-Z0-9]{9})', texto):
            datos["Assistencia"] = m.group(1).strip()
        if m := re.search(r'Telèfon\s*(\d{9})', texto):
            datos["Telefono"] = m.group(1).strip()
    
    if m := re.search(r'C.I.P.\s*([A-Z]{4}\d{10})', texto):
        datos["CIP"] = m.group(1).strip()

    return datos

def anonimizar_pdf(input_path, output_path):
    doc = fitz.open(input_path)

    # Extreure text global
    texto_global = ""
    for page in doc:
        texto_global += page.get_text()

    datos_encontrados = extraer_datos(texto_global)

    # Aplicar redaccion a cada página del PDF
    for page in doc:
        # Datos del paciente
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

        # Firmas
        for text in ["Médico Responsable del Alta", "Metge/essa Responsable de l'Alta"]:
            rects = page.search_for(text)
            if rects:
                y_inicio = rects[0].y0
                zona_a_ocultar = fitz.Rect(0, y_inicio, page.rect.width, page.rect.height)
                page.add_redact_annot(zona_a_ocultar, fill=(1, 1, 1))

        # Anotaciones colegiados
        anotaciones = re.findall(r'\d{2}/\d{2}/\d{2} \d{2}:\d{2} \([^)]+\)', page.get_text())

        for anotacion in anotaciones:
            # Solo redactamos el contenido entre paréntesis
            match = re.search(r'\(([^)]+)\)', anotacion)
            if match:
                texto_a_borrar = f"({match.group(1)})"
                rects = page.search_for(texto_a_borrar)
                for rect in rects:
                    page.add_redact_annot(rect, fill=(1, 1, 1))

    for page in doc:
        page.apply_redactions()

    doc.save(output_path, garbage=4, deflate=True)
    
# abrimos el CSV para registrar los nombres de los archivos originales y anonimizados
with open(CSV_LOG, mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["original","anonimizado"])

    # Para cada PDF en la carpeta de entrada ejectamos anonimizar_pdf() y guardamos en output folder
    contador = 1
    for file in os.listdir(INPUT_FOLDER):
        if file.lower().endswith(".pdf"):
            input_path = os.path.join(INPUT_FOLDER, file)
            output_filename = f"insuficiencia_ped_{contador}.pdf"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            anonimizar_pdf(input_path, output_path)
            writer.writerow([file, output_filename])
            contador += 1
print(f"✅ {contador-1} pdfs anonimizados en: {OUTPUT_FOLDER}")