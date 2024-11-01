from dash import dcc, html, Input, Output
import plotly.graph_objs as go


def layout():
    return html.Div([
        html.Div([
            dcc.Dropdown(
                id='interval-selector',
                options=[
                    {'label': '1 день', 'value': 1},
                    {'label': '3 дня', 'value': 3},
                    {'label': '5 дней', 'value': 5},
                ],
                value=5,
                clearable=False,
                style={'width': '80%', 'margin-bottom': '20px', 'margin-right': '40px'}
            ),
            dcc.Dropdown(
                id='graph-type',
                options=[
                    {'label': 'Температура', 'value': 'temperature'},
                    {'label': 'Ощущается как', 'value': 'real_feel'},
                    {'label': 'Влажность', 'value': 'humidity'},
                    {'label': 'Облачность', 'value': 'cloud_cover'},
                    {'label': 'Скорость ветра', 'value': 'wind'},
                    {'label': 'Вероятность осадков', 'value': 'precipitation'}
                ],
                value='temperature',
                clearable=False,
                style={'width': '80%', 'margin-bottom': '20px'}
            ),
        ], style={'display': 'flex', 'justify-content': 'center'}),

        html.Div(
            dcc.Graph(id='weather-forecast-graph'),
            style={'display': 'flex', 'justify-content': 'center'}
        )
    ])


def register_callbacks(dash_app):
    @dash_app.callback(
        Output('weather-forecast-graph', 'figure'),
        Input('interval-selector', 'value'),
        Input('graph-type', 'value')
    )
    def update_graph(days, graph_type):
        dash_data = dash_app.server.config.get('DASH_DATA')
        if not dash_data:
            return go.Figure().update_layout(title="Нет данных для отображения")

        days = days or 5
        dates = dash_data['dates'][:days]  # Обрезаем данные по числу дней

        if graph_type == 'temperature':
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=dash_data['max_temps'][:days], mode='lines+markers',
                                     name='Макс. температура', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['min_temps'][:days], mode='lines+markers',
                                     name='Мин. температура', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['day_real_feels'][:days], mode='lines+markers',
                                     name='Днём ощущается как', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['night_real_feels'][:days], mode='lines+markers',
                                     name='Ночью ощущается как', line={'shape': 'linear'}))

            fig.update_layout(title="Температура", yaxis_title="°C")

        elif graph_type == 'real_feel':
            fig = go.Figure(go.Scatter(x=dates, y=dash_data['day_real_feels'][:days], mode='lines+markers',
                                       name='Днём ощущается как', line={'shape': 'linear'}))
            fig.update_layout(title="Ощущается как", yaxis_title="°C")

        elif graph_type == 'precipitation':
            fig = go.Figure(go.Bar(x=dates, y=dash_data['precip_probs'][:days], name='Вероятность осадков'))

            fig.update_layout(title="Вероятность осадков", yaxis_title="%")

        elif graph_type == 'wind':
            fig = go.Figure(go.Scatter(x=dates, y=dash_data['wind_speeds'][:days], mode='lines+markers',
                                       name='Скорость ветра', line={'shape': 'linear'}))

            fig.update_layout(title="Скорость ветра", yaxis_title="км/ч")

        elif graph_type == 'humidity':
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=dates, y=dash_data['day_min_humidities'][:days], mode='lines+markers',
                                     name='Минимальная влажность днём', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['day_avg_humidities'][:days], mode='lines+markers',
                                     name='Средняя влажность днём', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['day_max_humidities'][:days], mode='lines+markers',
                                     name='Максимальная влажность днём', line={'shape': 'linear'}))

            fig.add_trace(go.Scatter(x=dates, y=dash_data['night_min_humidities'][:days], mode='lines+markers',
                                     name='Минимальная влажность ночью', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['night_avg_humidities'][:days], mode='lines+markers',
                                     name='Средняя влажность ночью', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['night_max_humidities'][:days], mode='lines+markers',
                                     name='Максимальная влажность ночью', line={'shape': 'linear'}))

            fig.update_layout(title="Влажность", yaxis_title="%")

        elif graph_type == 'cloud_cover':
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=dash_data['day_clouds'][:days], mode='lines+markers',
                                     name='Облачность днём', line={'shape': 'linear'}))
            fig.add_trace(go.Scatter(x=dates, y=dash_data['night_clouds'][:days], mode='lines+markers',
                                     name='Облачность ночью', line={'shape': 'linear'}))

            fig.update_layout(title="Облачность", yaxis_title="%")

        fig.update_layout(xaxis_title="Дата", template="plotly_dark")
        return fig
