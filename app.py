from datetime import timedelta

from flask import Flask, render_template, request, flash, session, redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from UserLogin import UserLogin
from db_models import db, Users, Roles, Tests, Topics, Results, TypeQuestions, Questions, Answers
from forms import LoginForm, RegisterForm
from test_process import Testing
from sqlalchemy import null

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


@app.errorhandler(401)
def pageNotFount(error):
    return render_template('page_for_401.html')


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page_for_404.html')


@login_manager.user_loader
def load_user(user_id):
    return UserLogin(user_id, db)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user.user)


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
            userLogin = UserLogin(user.id, db)
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
        session.pop('_flashes', None)
        if form.validate():
            exist = db.session.query(Users).filter(Users.email == form.email.data).all()
            if exist:
                flash("Пользователь с таким email существует", "error")
                return redirect(url_for('register', form=form))
            else:
                try:
                    teacher = 2 if form.teacher.data else 1
                    psw_hash = generate_password_hash(form.psw.data)
                    u = Users(email=form.email.data, psw=psw_hash,
                              name=form.name.data, role_id=teacher)
                    db.session.add(u)
                    db.session.commit()
                    flash("Вы успешно зарегистрированы", "success")
                    return redirect(url_for('login'))
                except:
                    flash("Произошла ошибка записи в базу данных", "error")
                    return redirect(url_for('register', form=form))
        # else:
        #     # flash("Неверно заполнены поля", "error")
        #     return redirect(url_for('register', form=form))

    return render_template("register.html", form=form)


@app.route('/topics')
def topics():
    all_topics = db.session.query(Topics).order_by(Topics.name).all()
    return render_template("topics.html", topics=all_topics)


@app.route('/tests_from_topic_<topic_id>')
def tests_from_topic(topic_id):
    if topic_id == 'no_topic':
        title = 'Тесты без категории'
        tests = db.session.query(Tests).filter(Tests.topic_id == None).all()
    elif topic_id == 'all':
        title = 'Все тесты'
        tests = db.session.query(Tests).all()
    elif topic_id == 'my':
        if not current_user.is_authenticated or current_user.user.id == 1:
            abort(401)
        title = 'Мои тесты'
        user = current_user.user
        tests = db.session.query(Tests).filter(Tests.author_id == user.id).all()
    else:
        try:
            topic_obj = db.session.query(Topics).get(topic_id)
            tests = topic_obj.tests_from_topic
            topic_name = topic_obj.name
            title = 'Тесты из ' + topic_name
        except:
            abort(404)
    return render_template('tests_from_topic.html', title=title, tests=tests)


@app.route('/test_preview_<test_id>')
@login_required
def test_preview(test_id):
    try:
        test = db.session.query(Tests).get(test_id)
    except:
        abort(404)
    user = current_user.user
    list_mark = db.session.query(Results).filter(Results.user_id == user.id, Results.test_id == test_id).all()
    try:
        best_mark = max(list_mark)
    except:
        best_mark = None
    return render_template('test_preview.html', test=test, best_mark=best_mark)


@app.route('/create_test', methods=["POST", "GET"])
@login_required
def create_test():
    db_topic = db.session.query(Topics).order_by(Topics.name).all()
    if request.method == 'POST':
        session.pop('_flashes', None)
        if len(request.form['name']) == 0 or len(request.form['num_stages']) == 0:
            flash("Не все поля заполнены", "error")
            return redirect(url_for('create_test'))
        else:
            try:
                exist = db.session.query(Tests).filter(Tests.name == request.form['name']).all()
                if exist:
                    flash("Это имя теста уже занято", "error")
                    return redirect(url_for('create_test'))
                else:
                    topic = int(request.form['topic'])
                    if topic == -1:
                        topic = None
                    new_test = Tests(name=request.form['name'], description=request.form['description'],
                                     author_id=current_user.user.id, topic_id=topic,
                                     num_stages=request.form['num_stages'])
                    db.session.add(new_test)
                    db.session.commit()
                    test = db.session.query(Tests).filter(Tests.name == request.form['name']).all()
                    return redirect(url_for('create_questions', test_id=test[0].id))
            except:
                flash("Ошибка подключения к базе данных", "error")
                return redirect(url_for('create_test'))
    return render_template('create_test.html', topics=db_topic)


@app.route('/create_questions_for_test_<test_id>')
def create_questions(test_id):
    types = db.session.query(TypeQuestions).all
    test = db.session.query(Tests).get(test_id)
    K = test.num_stages
    middle = (K+1)/2 if K%2 else K/2
    dict_level_count = {int(middle): K}
    for i in range(1, K+1):
        if i ==middle:
            pass
        elif i < middle:
            dict_level_count[i] = 2*i
        else:
            dict_level_count[i] = 2*(K-i)+1
    return render_template('create_questions.html', counts=dict_level_count, test_id=test_id, types=types)


# with app.test_request_context():
#     # db.drop_all()
#     db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
