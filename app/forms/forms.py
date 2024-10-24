from wtforms import Form, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class CityRouteForm(Form):
    start_city = StringField(
        'Начальная точка маршрута (город):',
        validators=[
            DataRequired(message="Название города обязательно"),
            Length(min=2, max=50, message="Название города должно быть от 2 до 50 символов"),
            Regexp(r'^[A-Za-zА-Яа-я\s]+$', message="Название города должно содержать только буквы")
        ]
    )

    end_city = StringField(
        'Конечная точка маршрута (город):',
        validators=[
            DataRequired(message="Название города обязательно"),
            Length(min=2, max=50, message="Название города должно быть от 2 до 50 символов"),
            Regexp(r'^[A-Za-zА-Яа-я\s]+$', message="Название города должно содержать только буквы")
        ]
    )

    submit = SubmitField('Проверить погоду')
