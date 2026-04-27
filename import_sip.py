import os
import sys
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_pyp_config.settings')
django.setup()

from django.contrib.auth.models import User
from cobranza.models import AgenteSIP

def import_sip_credentials(file_path):
    df = pd.read_excel(file_path)
    
    # Clean up column names in case of whitespace
    df.columns = df.columns.str.strip()
    
    # Find columns dynamically based on keywords
    user_col = next(c for c in df.columns if 'USUARIO' in c and 'CRM' in c)
    anexo_col = next(c for c in df.columns if 'Anexo' in c)
    clave_col = next(c for c in df.columns if 'Clave' in c or 'Contraseña' in c)
    
    success_count = 0
    missing_users = []
    
    for index, row in df.iterrows():
        username = str(row[user_col]).strip()
        anexo = str(row[anexo_col]).strip()
        clave = str(row[clave_col]).strip()
        
        if pd.isna(username) or username == 'nan' or not username:
            continue
            
        try:
            user = User.objects.get(username__iexact=username)
            # Create or update SIP profile
            AgenteSIP.objects.update_or_create(
                user=user,
                defaults={'anexo': anexo, 'clave': clave}
            )
            print(f"[OK] AgenteSIP guardado para: {user.username}")
            success_count += 1
        except User.DoesNotExist:
            print(f"[ERROR] Usuario no encontrado en DB: {username}")
            missing_users.append(username)
            
    print(f"\nResumen: {success_count} perfiles creados/actualizados.")
    if missing_users:
        print(f"Usuarios no encontrados: {missing_users}")

if __name__ == '__main__':
    import_sip_credentials('ANEXOS Y CLAVES.xlsx')
