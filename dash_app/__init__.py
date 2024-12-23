from dash import Dash, dcc, html
from .callbacks import register_callbacks
from .callbacks.callbacks import layout


def create_dash_app(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dash/'
    )

    dash_app.layout = layout()
    register_callbacks(dash_app)
    
    return dash_app
