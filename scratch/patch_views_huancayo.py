import os
import re

file_path = r'c:\CRM PYP\cobranza\views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to insert variables before defaults = {
target1 = "condicion_val = ''"

new_code1 = """condicion_val = ''
                            
                            # Nuevos campos de Convenio para Caja Huancayo
                            raw_fecha_pend = str(row.get('Fecha Pago Cuota Pendiente', '')).strip()
                            f_pend_val = safe_date(raw_fecha_pend) if raw_fecha_pend and raw_fecha_pend not in ('', 'nan', 'None') else None
                            
                            mca_str = str(row.get('Monto Cuota Atrasada', '0')).strip()
                            try:
                                mca_val = Decimal(mca_str.replace(',', ''))
                            except:
                                mca_val = Decimal('0')
                                
                            dias_atr_str = str(row.get('Días de Atraso de Cuota', str(row.get('Das de Atraso de Cuota', '0')))).strip()
                            try:
                                dias_atr_val = int(dias_atr_str)
                            except:
                                dias_atr_val = 0"""

content = content.replace(target1, new_code1)

target2 = "'negociacion': negociacion_str,"
new_code2 = """'negociacion': negociacion_str,
                                'cuota_pendiente': str(row.get('Cuota Pendiente', '')).strip(),
                                'total_cuotas': str(row.get('Total Cuotas (seg. Cronograma)', '')).strip(),
                                'fecha_pago_cuota_pendiente': f_pend_val,
                                'monto_cuota_atrasada': mca_val,
                                'credito_al_dia': str(row.get('¿Crédito al día?', str(row.get('Crdito al da?', str(row.get('Crédito al día', '')))))).strip(),
                                'dias_atraso_cuota': dias_atr_val,"""

if target2 in content:
    content = content.replace(target2, new_code2)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCH VIEWS.PY SUCCESS")
else:
    print("TARGET NOT FOUND")
