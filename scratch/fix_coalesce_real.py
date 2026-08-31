import re

file_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I want to fix all occurrences of Coalesce(..., 0.0) where the first argument is DecimalField
# We can just import Value and replace 0.0 with Value(0, output_field=DecimalField())

# First make sure Value is imported
if "from django.db.models import Value" not in content:
    content = content.replace("from django.db.models import Q,", "from django.db.models import Q, Value,")
    content = content.replace("from django.db.models import OuterRef, Subquery, Sum, Exists, Count, IntegerField, DecimalField", "from django.db.models import OuterRef, Subquery, Sum, Exists, Count, IntegerField, DecimalField, Value")

# Fix the specific Coalesce:
# monto_semana=Coalesce(Subquery(monto_semana_subquery, output_field=DecimalField()), 0.0),
content = content.replace("0.0),", "Value(0, output_field=DecimalField())),")

# Promesas vencidas is IntegerField:
# promesas_vencidas_cnt=Coalesce(Subquery(promesas_vencidas_subq, output_field=IntegerField()), 0)
# Here 0 is an int, which is fine for IntegerField.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Coalesce fixed!")
