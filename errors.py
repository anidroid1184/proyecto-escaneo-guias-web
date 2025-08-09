from flask import render_template, flash, redirect, request


def register_error_handlers(app):
    @app.errorhandler(413)
    def file_too_large(e):
        flash('El archivo es demasiado grande (máx 2MB).', 'danger')
        return redirect(request.url)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
