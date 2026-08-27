import os
import io

file_path = r"c:\CRM PYP\cobranza\whatsapp_views.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        nombre_archivo = f"WA_Masivo_{cartera}_{hoy.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        df.to_excel(response, index=False)
        return response"""

replacement = """        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='WhatsApp')
        
        output.seek(0)
        
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        nombre_archivo = f"WA_Masivo_{cartera}_{hoy.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        return response"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Target not found")
