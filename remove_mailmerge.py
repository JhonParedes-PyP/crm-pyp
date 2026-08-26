from docx import Document
import os

def remove_mailmerge(doc_path):
    doc = Document(doc_path)
    settings = doc.settings._element
    mail_merges = settings.xpath('.//w:mailMerge')
    for mm in mail_merges:
        mm.getparent().remove(mm)
    doc.save(doc_path)
    print("Mail merge removed from", doc_path)

if __name__ == '__main__':
    remove_mailmerge(r'C:\CRM PYP\plantilla_caja_huancayo_v2.docx')
