from flask import Flask
from app.routes import weather_blueprint, errors_blueprint


def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static', static_url_path='/static')

    app.register_blueprint(weather_blueprint)
    app.register_blueprint(errors_blueprint)

    return app
