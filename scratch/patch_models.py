import os

file_path = r"c:\CRM PYP\cobranza\models.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add score field before 'class Meta'
score_field = """
    # CAMPO DE IA SCORING
    score = models.IntegerField(default=10, help_text="Puntaje AI de Probabilidad de Pago")

    class Meta:"""

content = content.replace("    class Meta:", score_field)

# 2. Add actualizar_score and save to Deudor
methods_code = """
    def __str__(self):
        return self.nombre_completo

    def actualizar_score(self, commit=True):
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
        super(Deudor, self).save(*args, **kwargs)
"""

content = content.replace("""    def __str__(self):
        return self.nombre_completo""", methods_code)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("models.py patched!")
