from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль",
                        validators=[DataRequired(),
                                    Length(min=4, max=100,
                                           message="Пароль должен быть от 4 до 100 символов")])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    name = StringField("Имя",
                       validators=[DataRequired(),
                                   Length(min=4, max=100,
                                          message="Имя должно быть от 4 до 100 символов")])
    email = EmailField("Email", validators=[DataRequired(), Email("Некорректный email")])
    psw = PasswordField("Пароль",
                        validators=[DataRequired(),
                                    Length(min=4, max=100,
                                           message="Пароль должен быть от 4 до 100 символов")])
    psw2 = PasswordField("Повторите пароль",
                         validators=[DataRequired(),
                                     EqualTo('psw', message="Пароли не совпадают")])
    teacher = BooleanField("Учитель", default=False)
    submit = SubmitField("Регистрация")

#
# class TestInfoForm(FlaskForm):
#     name = StringField("Название теста",
#                        validators=[DataRequired(),
#                                    Length(min=4, max=150,
#                                           message="Имя должно быть от 4 до 150 символов")])
#     description = TextAreaField("Описание теста (не обязательно)", validators=[Length(max=500)])
#     num_stages = IntegerField('Число стадий', validators=[DataRequired()])
#     submit = SubmitField("Далее")
