# Proyecto: Escaneo y Control de Guías Web

Sistema web para registrar, editar y controlar guías mediante escaneo o ingreso manual de códigos. Accesible desde móvil y escritorio.

## Características principales

- Registro y edición de guías por escaneo o ingreso manual
- Alta masiva desde Excel
- Persistencia en SQLite (fácil de migrar a MySQL)
- Exportación de registros a Excel
- Interfaz responsive (Bootstrap 5)
- Escaneo con cámara usando html5-qrcode

## Estructura del Proyecto

```
├── app.py
├── config.py
├── errors.py
├── forms.py
├── init_db.py
├── models.py
├── requirements.txt
├── run_app.py
├── utils.py
├── wsgi.py
├── LICENSE
├── README.md
├── /routes
├── /static
├── /templates
├── /uploads
├── /exports
├── /instance
```

## Despliegue en PythonAnywhere (Guía para el Cliente)

1. **Sube el proyecto a tu cuenta de PythonAnywhere**
2. **Crea un entorno virtual:**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Crea las carpetas necesarias:**
   ```bash
   mkdir -p uploads exports instance
   ```
4. **Inicializa la base de datos:**
   ```bash
   python init_db.py
   ```
5. **Configura el archivo WSGI:**
   - En el panel de PythonAnywhere, ve a Web > WSGI configuration file.
   - Asegúrate que el contenido sea similar a:
     ```python
     import sys
     import os
     project_home = '/home/<tu_usuario>/proyecto-escaneo-guias-web'
     if project_home not in sys.path:
         sys.path = [project_home] + sys.path
     from app import app as application
     ```
6. **Configura la ruta de archivos estáticos y media en PythonAnywhere:**
   - Añade rutas para `/static/`, `/uploads/` y `/exports/`.
7. **Reinicia la web app desde el panel de PythonAnywhere.**

## Notas para producción

- Por defecto usa SQLite. Si necesitas MySQL, cambia la URI en `config.py`.
- El archivo `LICENSE` permite uso comercial solo al cliente final.

## Créditos y Licencia

- Autor: Juan Valencia (anidroid1184)
- Cliente: Uso exclusivo para el cliente final según acuerdo comercial.
- Licencia: Comercial, ver archivo LICENSE.

---

© 2025 Juan Valencia. Todos los derechos reservados. 5. **Inicializa la base de datos:**

```bash
python app.py  # Se creará app.db automáticamente al iniciar
```

6. **Ejecuta la aplicación:**
   ```bash
   flask run
   # o
   python app.py
   ```

## Uso

- Accede a `http://localhost:5000` desde tu navegador.
- Escanea un código de barras o ingrésalo manualmente.
- Si la persona no existe, regístrala desde el formulario.
- Carga personas masivamente desde Excel/CSV en la sección "Cargar Excel".
- Visualiza y filtra registros en "Ver Registros".
- Exporta los registros filtrados a Excel desde "Exportar".

## Formato de Excel/CSV para carga masiva

El archivo debe tener las columnas:

- `nombre`
- `documento`
- `codigo_barras`

## Consideraciones de Seguridad

- Solo se permiten archivos `.xlsx` y `.csv` de hasta 2MB.
- Los datos se validan y sanitizan antes de ser almacenados.
- No compartas la base de datos ni los archivos exportados sin autorización.

## Dependencias principales

- Flask
- Flask-SQLAlchemy
- Flask-WTF
- pandas
- openpyxl
- Bootstrap 5 (CDN)
- html5-qrcode (CDN)

## Personalización

- Cambia la clave secreta en `app.py` para producción.
- Puedes migrar a PostgreSQL cambiando la URI de la base de datos.

## Licencia

MIT
