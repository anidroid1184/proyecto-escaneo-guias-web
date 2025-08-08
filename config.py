import os


class Config:
    SECRET_KEY = 'clave_prueba'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    EXPORT_FOLDER = os.path.join(os.getcwd(), 'exports')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB máximo por archivo
    ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
