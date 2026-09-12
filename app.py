from flask import Flask, render_template
from mysql.connector import Error as MySQLError

from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.doctor import doctor_bp
    from routes.main import main_bp
    from routes.patient import patient_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(MySQLError)
    def database_error(error):
        app.logger.error("Database error: %s", error)
        return render_template("error.html", message="The database is temporarily unavailable."), 503

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="The page you requested was not found."), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
