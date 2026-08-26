import pandas as pd

def safe_date(valor):
    raw = str(valor).strip()
    if raw in ('', 'nan', 'None', 'NaT'):
        return None
    try:
        if '-' in raw and len(raw) >= 10 and raw[4] == '-':
            resultado = pd.to_datetime(raw, errors='coerce')
        else:
            resultado = pd.to_datetime(raw, dayfirst=True, errors='coerce')
        if pd.isna(resultado):
            return None
        return resultado.date()
    except Exception:
        return None

def fix_excel_date(raw):
    raw = str(raw).strip()
    # If YYYY-MM-DD
    if '-' in raw and len(raw) >= 10 and raw[4] == '-':
        parts = raw[:10].split('-')
        if len(parts) == 3:
            # swap month and day if both <= 12
            if int(parts[1]) <= 12 and int(parts[2]) <= 12:
                raw = f"{parts[0]}-{parts[2]}-{parts[1]}"
    # If DD/MM/YYYY or MM/DD/YYYY
    elif '/' in raw:
        parts = raw.split()[0].split('/') # get just the date part, ignore time
        if len(parts) == 3:
            # check if day and month are both <= 12
            if parts[0].isdigit() and parts[1].isdigit():
                if int(parts[0]) <= 12 and int(parts[1]) <= 12:
                    # swap them
                    raw = f"{parts[1]}/{parts[0]}/{parts[2]}"
    
    return safe_date(raw)

print(fix_excel_date('01/12/2026')) # should be 2026-01-12
print(fix_excel_date('25/01/2026')) # should be 2026-01-25
print(fix_excel_date('2026-12-01 00:00:00')) # should be 2026-01-12
