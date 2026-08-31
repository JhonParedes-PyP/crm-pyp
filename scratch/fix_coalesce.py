import os

file_path = r"c:\CRM PYP\cobranza\dashboard_views.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace float 0.0 with Value(0, output_field=DecimalField())
old = "monto_semana=Coalesce(Subquery(monto_semana_subquery, output_field=DecimalField()), 0.0)"
new = "monto_semana=Coalesce(Subquery(monto_semana_subquery, output_field=DecimalField()), Value(0, output_field=DecimalField()))"

if old in content:
    content = content.replace(old, new)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed Coalesce in dashboard_views.py")
else:
    print("Could not find the Coalesce line.")
