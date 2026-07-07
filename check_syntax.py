import sys
import py_compile
try:
    py_compile.compile('cobranza/middleware.py', doraise=True)
    print("middleware.py is valid")
except Exception as e:
    print(f"middleware.py ERROR: {e}")

try:
    py_compile.compile('cobranza/dashboard_views.py', doraise=True)
    print("dashboard_views.py is valid")
except Exception as e:
    print(f"dashboard_views.py ERROR: {e}")
