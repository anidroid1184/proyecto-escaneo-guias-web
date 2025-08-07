# Control de Accesos por Código de Barras

Sistema web ligero para registrar ingresos y salidas de personas mediante escaneo de códigos de barras o ingreso manual. Accesible desde móvil y escritorio.

## Características

- Registro de entradas y salidas por escaneo o ingreso manual
- Alta manual y masiva de personas (Excel/CSV)
- Persistencia en SQLite (SQLAlchemy)
- Exportación de registros a Excel
- Interfaz responsive (Bootstrap 5)
- Escaneo con cámara usando html5-qrcode

## Estructura del Proyecto

```
/project_root
│
├── app.py
├── models.py
├── forms.py
├── requirements.txt
│
├── /templates
│   ├── base.html
│   ├── upload.html
│   ├── index.html
│   ├── register.html
│   └── registros.html
│
├── /static
│   ├── /css/custom.css
│   └── /js/scanner.js
│
├── /uploads
├── /exports
├── app.db
└── README.md
```

## Instalación

1. **Clona el repositorio y entra al directorio:**
   ```bash
   git clone <url-del-repo>
   cd proyecto-escaneo-guias-web
   ```
2. **Crea un entorno virtual (opcional pero recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Crea las carpetas necesarias:**
   ```bash
   mkdir uploads exports
   ```
5. **Inicializa la base de datos:**
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
