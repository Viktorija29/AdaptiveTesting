from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField,\
                    PasswordField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[Email()])
    psw = PasswordField("Пароль", validators=[DataRequired(),
                                              Length(min=4, max=100)])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(),
                                          Length(min=4, max=100)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    psw = PasswordField("Пароль", validators=[DataRequired(),
                                              Length(min=4, max=100)])
    psw2 = PasswordField("Повторите пароль",
                         validators=[DataRequired(),
                                     EqualTo('psw',
                                             message="Пароли отличаются")])
    teacher = BooleanField("Учитель", default=False)
    submit = SubmitField("Регистрация")
