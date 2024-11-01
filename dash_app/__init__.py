from dash import Dash, dcc, html
from .callbacks import register_callbacks
from .callbacks.callbacks import layout


def create_dash_app(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dash/'
    )

    dash_app.layout = html.Div([
        html.H1("Погодный прогноз", style={'text-align': 'center', 'color': '#00adb5'}),

        dcc.Dropdown(
            id='interval-selector',
            options=[
                {'label': 'Последний день', 'value': 1},
                {'label': 'Последние 3 дня', 'value': 3},
                {'label': 'Последние 5 дней', 'value': 5},
            ],
            value=5,
            clearable=False,
            style={'width': '80%', 'margin': '20px auto'}
        ),

        dcc.Dropdown(
            id='graph-type',
            options=[
                {'label': 'Температура', 'value': 'temperature'},
                {'label': 'Осадки', 'value': 'precipitation'},
                {'label': 'Ветер', 'value': 'wind'}
            ],
            value='temperature',
            clearable=False,
            style={'width': '80%', 'margin': '20px auto'}
        ),

        dcc.Graph(id='weather-forecast-graph')
    ])

    dash_app.layout = layout()
    register_callbacks(dash_app)
    
    return dash_app
