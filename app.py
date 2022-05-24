from flask import Flask, render_template, request, flash, session, redirect, url_for
from forms import LoginForm, RegisterForm
from datetime import datetime, timedelta
from db_models import db, Users
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin

# создание экземпляра приложения
app = Flask(__name__)
# связывает SQLAlchemy с той или иной СУБД
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2504@localhost/adaptive_testing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '22548492a9db86a83757dbfae78c8521e69ecdbf'
# сколько браузер будет хранить remember me в куки
# пока хранится - устаревшие session будут обновляться
# app.config["REMEMBER_COOKIE_DURATION"] = timedelta(seconds=10000)
# через сколько устаревает session в куки

# хранит пользователя в течение 30 минут, если тот не совершает никаких действий
# иначе, обновляется и снова 30 минут
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# создание экземпляра SQLALCHEMY, передается ссылка на app
db.init_app(app)


# экземпляр класса LoginManager управляет процессом аторизации
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().getUserFromDB(user_id, db)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('login'))


@app.route('/')
def index():
    return 'index page'


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user.user)

#
# @app.route('/log')
# @login_required
# def index_log():
#     return f"""вы вошли
#                <p><a href='{url_for('logout')}'> Выйти </a></p>
#                 <p>Сессии: {session} </p>
#                 <p>Куки: {request.cookies}</p>"""


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if request.method == "POST":
        session.pop('_flashes', None)
        # если его нет - вернет None и дальше не идет
        user = db.session.query(Users).filter(Users.email == form.email.data).first()
        if user and check_password_hash(user.psw, form.psw.data):
            userLogin = UserLogin().create(user)
            # авторизация в сессии
            login_user(userLogin)
            session.permanent = True
            return redirect(url_for('profile'))
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html', form=form)


# потестить все и сделать норм сообщения об ошибках
@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        # session.pop('_flashes', None)
        if form.validate():
            exist = db.session.query(Users).filter(Users.email == form.email.data).all()
            if exist:
                # flash("Пользователь с таким email существует", "error")
                return redirect(url_for('register', form=form))
            else:
                try:
                    teacher = 2 if form.teacher.data else 1
                    psw_hash = generate_password_hash(form.psw.data)
                    u = Users(email=form.email.data, psw=psw_hash,
                              name=form.name.data, role=teacher)
                    db.session.add(u)
                    db.session.commit()
                    flash("Вы успешно зарегистрированы", "success")
                    return redirect(url_for('login'))
                except:
                    # flash("Произошла ошибка записи в базу данных", "error")
                    # return redirect(url_for('register', form=form))
                    print('err')
        # else:
        #     # flash("Неверно заполнены поля", "error")
        #     return redirect(url_for('register', form=form))

    return render_template("register.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
