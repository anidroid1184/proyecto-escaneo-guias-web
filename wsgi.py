import sys
import os

# Cambia este path por el de tu usuario en PythonAnywhere
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cargar la app Flask desde app.py
from app import app as application
