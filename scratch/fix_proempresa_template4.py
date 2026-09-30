from docx import Document

def fix_proempresa_template4():
    doc = Document(r'c:\CRM PYP\MODELO DE CARTA DE PROEMPRESA.docx')
    for p in doc.paragraphs:
        if "Lima          , de                 de 2025" in p.text:
            p.text = p.text.replace("Lima          , de                 de 2025", "Lima,                                           ")
            
    doc.save(r'c:\CRM PYP\MODELO DE CARTA DE PROEMPRESA.docx')
    print("TEMPLATE UPDATED SUCCESSFULLY 4")

if __name__ == "__main__":
    fix_proempresa_template4()
