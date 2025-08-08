import os
from flask import Flask
from models import db
from config import Config
from routes.main import main_bp
from routes.scan import scan_bp
from routes.register import register_bp
from routes.records import records_bp
from routes.session import session_bp
import errors  # Importar el módulo de errores para registrar los manejadores


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

# Crear carpetas necesarias si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
