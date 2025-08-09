import os
import sys
from dotenv import load_dotenv
from app import app as application  # PythonAnywhere espera 'application'

# Añadir la ruta de su proyecto al path de Python
# Asegúrese de reemplazar 'su_usuario' con su nombre de usuario real de
# PythonAnywhere
project_home = '/home/su_usuario/proyecto-escaneo-guias-web'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cargar variables de entorno desde .env si existe (para desarrollo local)
# En PythonAnywhere, las variables de entorno se configuran directamente
# en el dashboard
dotenv_path = os.path.join(project_home, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# La aplicación Flask se importa como 'application' para PythonAnywhere
# No es necesario hacer nada más aquí, ya que 'application' ya está definida.
