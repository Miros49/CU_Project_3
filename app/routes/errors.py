from flask import Blueprint, render_template

errors_blueprint = Blueprint('errors', __name__)


@errors_blueprint.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@errors_blueprint.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


@errors_blueprint.app_errorhandler(503)
def service_unavailable(e):
    return render_template('errors/503.html'), 503
