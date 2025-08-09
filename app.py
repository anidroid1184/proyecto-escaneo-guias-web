import os
from flask import Flask
from models import db
from config import Config
from routes.main import main_bp
from routes.scan import scan_bp
from routes.register import register_bp
from routes.records import records_bp
from routes.session import session_bp
from dotenv import load_dotenv
from errors import (
    register_error_handlers
)  # Importar la función de registro de errores

load_dotenv()  # Cargar variables de entorno desde .env


app = Flask(__name__)
app.config.from_object(Config)

# Inicializar SQLAlchemy
with app.app_context():
    db.init_app(app)
    db.create_all()

# Registrar Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(register_bp)
app.register_blueprint(records_bp)
app.register_blueprint(session_bp)

# Registrar manejadores de errores
register_error_handlers(app)

# Crear carpetas necesarias si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    # Configuración para producción (comentada para desarrollo local)
    app.run(debug=False, host='0.0.0.0', port=8000)

    # Configuración para desarrollo local
    # app.run(debug=True, host='127.0.0.1', port=5000)
