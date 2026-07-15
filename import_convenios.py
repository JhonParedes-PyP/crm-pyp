import os
import django
import pandas as pd
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_pyp_config.settings")
django.setup()

from cobranza.models import Deudor, Convenio

def importar_convenios(file_path):
    print(f"Borrando convenios anteriores...")
    Convenio.objects.all().delete()

    print(f"Leyendo {file_path}...")
    df = pd.read_excel(file_path)
    
    # Manejar NaN
    df = df.fillna('')
    
    agregados = 0
    no_encontrados = 0
    
    for index, row in df.iterrows():
        cuenta = str(row.get('Cuenta', '')).strip()
        if not cuenta:
            continue
            
        deudores = Deudor.objects.filter(cuenta=cuenta)
        if deudores.exists():
            deudor = deudores.first()
            
            # Fecha de pago
            fecha_pago_raw = row.get('Fecha Pago Cuota Pendiente', '')
            fecha_pago = None
            if pd.notnull(fecha_pago_raw) and fecha_pago_raw != '':
                try:
                    fecha_pago = pd.to_datetime(fecha_pago_raw).date()
                except:
                    pass
            
            # Monto cuota
            monto_raw = row.get('Monto Cuota Atrasada', '')
            monto_cuota = 0.0
            if monto_raw != '':
                try:
                    monto_cuota = float(monto_raw)
                except:
                    pass
            
            # Dias atraso
            dias_raw = row.get('Días de Atraso de Cuota', '')
            dias_atraso = 0
            if dias_raw != '':
                try:
                    dias_atraso = int(dias_raw)
                except:
                    pass
                    
            Convenio.objects.create(
                deudor=deudor,
                cuenta=cuenta,
                cuota_pendiente=str(row.get('Cuota Pendiente', '')),
                fecha_pago=fecha_pago,
                monto_cuota=monto_cuota,
                dias_atraso=dias_atraso,
                situacion=str(row.get('SITUACION DEL COVENIO', ''))
            )
            agregados += 1
        else:
            no_encontrados += 1
            
    print(f"Completado! Agregados: {agregados}. No encontrados en cartera: {no_encontrados}.")

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), 'CONVENIOS.xlsx')
    if os.path.exists(file_path):
        importar_convenios(file_path)
    else:
        print(f"No se encontró el archivo: {file_path}")
