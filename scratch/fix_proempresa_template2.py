from docx import Document

def fix_template2():
    doc = Document(r'c:\CRM PYP\MODELO DE CARTA DE PROEMPRESA.docx')
    
    for p in doc.paragraphs:
        if "CANCELACIÓN HASTA" in p.text.upper():
            p.text = "CANCELACIÓN HASTA EL:                                                "
            
    doc.save(r'c:\CRM PYP\MODELO DE CARTA DE PROEMPRESA.docx')
    print("TEMPLATE CANCELACION FIXED")

if __name__ == "__main__":
    fix_template2()
