from flask import Blueprint, render_template

errors_blueprint = Blueprint('errors', __name__)


def render_error_template(code):
    return render_template(f'errors/{code}.html'), code


@errors_blueprint.app_errorhandler(404)
@errors_blueprint.app_errorhandler(429)
@errors_blueprint.app_errorhandler(500)
@errors_blueprint.app_errorhandler(503)
def handle_errors(e):
    code = getattr(e, 'code', 500)
    return render_error_template(code)
