import os

file_path = r"c:\CRM PYP\cobranza\models.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I will replace the score logic in save and actualizar_score to use convenio_set.exists()
# Since we already patched models.py once, I'll use regex or string replace for the whole methods block.

old_logic = """    def actualizar_score(self, commit=True):
        from datetime import date
        puntaje = 10  # Base
        
        # Regla 1: Convenio o Negociacion activa
        c_upper = str(self.condicion).upper()
        if 'CONVENIO' in c_upper or (self.negociacion and len(self.negociacion.strip()) > 3):
            puntaje += 40
            
        # Regla 2: Ultimo dia de pago
        if self.ultimo_dia_pago:
            dias_desde_pago = (date.today() - self.ultimo_dia_pago).days
            if dias_desde_pago <= 30:
                puntaje += 40
            elif dias_desde_pago <= 60:
                puntaje += 20
                
        # Regla 3: Si tiene una promesa reciente (en las gestiones) 
        # (Esto requeriría buscar Gestiones, que es pesado. Mejor dejamos 
        # el puntaje de promesa para cuando se crea la Gestion)
        
        # Tope 100
        if puntaje > 100:
            puntaje = 100
            
        self.score = puntaje
        if commit:
            self.save(update_fields=['score'])
            
    def save(self, *args, **kwargs):
        # Siempre recalcular el score al guardar si no se especifican update_fields (evitar loop infinito)
        if not kwargs.get('update_fields'):
            from datetime import date
            puntaje = 10
            c_upper = str(self.condicion).upper()
            if 'CONVENIO' in c_upper or (self.negociacion and len(self.negociacion.strip()) > 3):
                puntaje += 40
            if self.ultimo_dia_pago:
                dias_desde_pago = (date.today() - self.ultimo_dia_pago).days
                if dias_desde_pago <= 30:
                    puntaje += 40
                elif dias_desde_pago <= 60:
                    puntaje += 20
            self.score = min(puntaje, 100)
        super(Deudor, self).save(*args, **kwargs)"""

new_logic = """    def actualizar_score(self, commit=True):
        from datetime import date
        puntaje = 10  # Base
        
        # Regla 1: Convenio activo o negociacion en la base
        c_upper = str(self.condicion).upper()
        tiene_convenio = False
        if self.id:  # Only if it's already saved in DB
            tiene_convenio = self.convenio_set.exists()
            
        if tiene_convenio or 'CONVENIO' in c_upper or (self.negociacion and len(self.negociacion.strip()) > 3):
            puntaje += 40
            
        # Regla 2: Ultimo dia de pago
        if self.ultimo_dia_pago:
            dias_desde_pago = (date.today() - self.ultimo_dia_pago).days
            if dias_desde_pago <= 60:
                puntaje += 40
            elif dias_desde_pago <= 180:
                puntaje += 20
            else:
                puntaje += 10 # Al menos pagó alguna vez
                
        self.score = min(puntaje, 100)
        if commit:
            self.save(update_fields=['score'])
            
    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            from datetime import date
            puntaje = 10
            
            c_upper = str(self.condicion).upper()
            tiene_convenio = False
            if self.id:
                tiene_convenio = self.convenio_set.exists()
                
            if tiene_convenio or 'CONVENIO' in c_upper or (self.negociacion and len(self.negociacion.strip()) > 3):
                puntaje += 40
                
            if self.ultimo_dia_pago:
                dias_desde_pago = (date.today() - self.ultimo_dia_pago).days
                if dias_desde_pago <= 60:
                    puntaje += 40
                elif dias_desde_pago <= 180:
                    puntaje += 20
                else:
                    puntaje += 10
            self.score = min(puntaje, 100)
        super(Deudor, self).save(*args, **kwargs)"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("models.py logic improved!")
else:
    print("Could not find the old logic!")
