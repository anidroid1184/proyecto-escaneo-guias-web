import os


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY', 'una_clave_secreta_muy_segura_para_produccion'
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    EXPORT_FOLDER = os.path.join(os.getcwd(), 'exports')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB máximo por archivo
    ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
