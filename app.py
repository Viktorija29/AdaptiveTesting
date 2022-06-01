from datetime import timedelta
from os import remove
import pickle
import random

from flask import Flask, render_template, request, flash, session, \
    redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required, \
    logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from UserLogin import UserLogin
from db_models import db, Users, Roles, Tests, Topics, Results, \
    TypeQuestions, Questions, Answers
from forms import LoginForm, RegisterForm
from test_process import Testing

# создание экземпляра приложения
app = Flask(__name__)
# связывает SQLAlchemy и СУБД
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://postgres:2504@localhost/adaptive_testing'
# секретный ключ
app.config['SECRET_KEY'] = '22548492a9db86a83757dbfae78c8521e69ecdbf'
# указывает сколько времени браузер хранит данные пользователя,
# пока он не совершает никаких действий
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# создание экземпляра SQLALCHEMY, передается ссылка на app
db.init_app(app)

# экземпляр класса LoginManager управляет процессом авторизации
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
        user = db.session.query(Users). \
            filter(Users.email == form.email.data).first()
        if user and check_password_hash(user.psw, form.psw.data):
            userLogin = UserLogin(user.id, db)
            # авторизация в сессии
            login_user(userLogin)
            session.permanent = True
            return redirect(url_for('profile'))
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html', form=form)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        session.pop('_flashes', None)
        if form.validate():
            exist = db.session.query(Users). \
                filter(Users.email == form.email.data).all()
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
    return render_template("register.html", form=form)


@app.route('/topics')
def topics():
    all_topics = db.session.query(Topics).order_by(Topics.name).all()
    return render_template("topics.html", topics=all_topics)


@app.route('/tests_from_topic_<topic_id>')
def tests_from_topic(topic_id):
    if topic_id == 'no_topic':
        title = 'Тесты без категории'
        tests = db.session.query(Tests). \
            filter(Tests.topic_id == None).all()
    elif topic_id == 'all':
        title = 'Все тесты'
        tests = db.session.query(Tests).all()
    elif topic_id == 'my':
        if not current_user.is_authenticated or current_user.user.id == 1:
            abort(401)
        title = 'Мои тесты'
        user = current_user.user
        tests = db.session.query(Tests). \
            filter(Tests.author_id == user.id).all()
    else:
        try:
            topic_obj = db.session.query(Topics).get(topic_id)
            tests = topic_obj.tests_from_topic
            topic_name = topic_obj.name
            title = 'Тесты из ' + topic_name
        except:
            abort(404)
    return render_template('tests_from_topic.html',
                           title=title, tests=tests)


@app.route('/test_preview_<test_id>')
@login_required
def test_preview(test_id):
    try:
        test = db.session.query(Tests).get(test_id)
    except:
        abort(404)
    user = current_user.user
    results = db.session.query(Results). \
        filter(Results.user_id == user.id,
               Results.test_id == test_id).all()
    list_mark, list_points = [], []
    for r in results:
        list_mark.append(r.mark)
        list_points.append(r.points)
    all_questions = test.all_questions
    try:
        best_mark = max(list_mark)
        best_points = max(list_points)
    except:
        best_mark, best_points = None, None
    return render_template('test_preview.html', best_points=best_points,
                           test=test, all_questions=all_questions,
                           best_mark=best_mark)


@app.route('/create_test', methods=["POST", "GET"])
@login_required
def create_test():
    if current_user.user.role_id != 2:
        abort(401)
    db_topic = db.session.query(Topics).order_by(Topics.name).all()
    if request.method == 'POST':
        session.pop('_flashes', None)
        if len(request.form['name']) == 0 or \
                len(request.form['num_stages']) == 0:
            flash("Не все поля заполнены", "error")
            return redirect(url_for('create_test'))
        else:
            try:
                exist = db.session.query(Tests).\
                    filter(Tests.name == request.form['name']).all()
                if exist:
                    flash("Это имя теста уже занято", "error")
                    return redirect(url_for('create_test'))
                else:
                    topic = int(request.form['topic'])
                    if topic == -1:
                        topic = None
                    new_test = Tests(name=request.form['name'],
                                     description=request.form['description'],
                                     author_id=current_user.user.id,
                                     num_stages=request.form['num_stages'],
                                     topic_id=topic)
                    db.session.add(new_test)
                    db.session.commit()
                    test = db.session.query(Tests).\
                        filter(Tests.name == request.form['name']).all()
                    return redirect(url_for('create_questions',
                                            test_id=test[0].id))
            except:
                flash("Ошибка подключения к базе данных", "error")
                return redirect(url_for('create_test'))
    return render_template('create_test.html', topics=db_topic)


@app.route('/create_questions_for_test_<test_id>', methods=["POST", "GET"])
@login_required
def create_questions(test_id):
    if current_user.user.role_id != 2 or\
            current_user.user.id !=\
            db.session.query(Tests).get(test_id).author_of_test.id:
        abort(401)
    types = db.session.query(TypeQuestions).all()
    test = db.session.query(Tests).get(test_id)
    K = test.num_stages
    middle = (K + 1) / 2 if K % 2 else K / 2
    level_count = {}
    for i in range(1, K + 1):
        if i == middle:
            level_count[int(middle)] = K
        elif i < middle:
            level_count[i] = 2 * i
        else:
            level_count[i] = 2 * (K - i) + 1
    list_keys = list(level_count.keys())
    list_keys.sort()
    if request.method == "POST":
        list_questions = []
        for lev in list_keys:
            for q_num in range(level_count[lev]):
                text_question = request.form[f"{lev}_{q_num}"]
                type_id = request.form[f"type_{lev}_{q_num}"]
                question = Questions(text=text_question,
                                     test_id=test_id,
                                     type_id=type_id,
                                     difficulty_level=lev)
                list_questions.append(question)
        db.session.add_all(list_questions)
        db.session.commit()
        return redirect(url_for('setting_answers', test_id=test_id))

    return render_template('create_questions.html', level_count=level_count,
                           test_id=test_id, types=types, list_keys=list_keys)


@app.route('/setting_answers_for_test_<test_id>', methods=["POST", "GET"])
@login_required
def setting_answers(test_id):
    if current_user.user.role_id != 2 or current_user.user.id !=\
            db.session.query(Tests).get(test_id).author_of_test.id:
        abort(401)
    all_questions = db.session.query(Tests).get(test_id).all_questions
    if request.method == "POST":
        # словать типа id-question : count_answers
        list_q_count = {}
        for q in request.form.keys():
            list_q_count[int(q)] = int(request.form[q])
        return render_template('setting_answers.html', mode='create',
                               all_questions=all_questions,
                               list_q_count=list_q_count, test_id=test_id)
    return render_template('setting_answers.html', mode='setting',
                           all_questions=all_questions, test_id=test_id)


@app.route('/create_answers_for_test_<test_id>', methods=["POST"])
@login_required
def create_answers(test_id):
    if current_user.user.role_id != 2 or current_user.user.id !=\
            db.session.query(Tests).get(test_id).author_of_test.id:
        abort(401)
    all_questions = db.session.query(Tests).get(test_id).all_questions
    answers = []
    for q in all_questions:
        for k in request.form.keys():
            if f'input_{q.id}' in k:
                (_, _, id_input_in_q) = k.rpartition('_')
                if q.type_id == 1:
                    correct = request.form[f"radio_{q.id}"] ==\
                              f"{q.id}_{id_input_in_q}"
                elif q.type_id == 2:
                    correct =\
                        f"checkbox_{q.id}_{id_input_in_q}" in request.form
                answers.append(Answers(answer_text=request.form[k],
                                       question_id=q.id, correctness=correct))
    db.session.add_all(answers)
    db.session.commit()
    return redirect(url_for('tests_from_topic', topic_id='my'))


@app.route('/process_testing_<test_id>', methods=["GET", "POST"])
@login_required
def process_testing(test_id):
    if current_user.user.role_id != 1:
        abort(401)
    path = f'testing/testing_{test_id}_{current_user.user.id}.txt'
    try:
        file = open(path, 'rb')
    except IOError as e:
        file = open(path, 'wb')
        file.close()
        file = open(path, 'rb')
    try:
        testing = pickle.load(file)
    except EOFError as e:
        testing = None
    file.close()
    if not testing:
        testing = Testing(test=db.session.query(Tests).get(test_id))
    if testing.current_stage > testing.test.num_stages:
        results = Results(user_id=current_user.user.id, test_id=int(test_id),
                          points=round(testing.points /
                                       testing.test.num_stages * 100, 2),
                          mark=testing.current_level)
        db.session.add(results)
        db.session.commit()
        remove(path)
        return redirect(url_for('test_preview', test_id=test_id))
    question = testing.current_question
    if request.method == "POST":
        res = 0
        if question.type_id == 1:
            id_answer = int(request.form["radio_answer"])
            res = db.session.query(Answers).get(id_answer).correctness
            testing.points += 1 if res else 0
        elif question.type_id == 2:
            true_vars = 0
            false_vars = 0
            answers_for_question = db.session.query(Answers).\
                filter(Answers.question_id == question.id).all()
            count_correct = db.session.query(Answers).\
                filter(Answers.question_id == 112, Answers.correctness).count()
            for answer in answers_for_question:
                if f'checkbox_{answer.id}' in request.form.keys():
                    res_ans = db.session.query(Answers).\
                        get(answer.id).correctness
                    if res_ans:
                        true_vars += 1
                    else:
                        false_vars += 1
            res = max(0, (true_vars - false_vars) / count_correct)
            testing.points += res
            res = 0 if res < 0.5 else 1
        if res:
            if testing.current_sub_level == 2:
                testing.current_sub_level = 1
                testing.current_level += 1
            else:
                testing.current_sub_level = 2
        else:
            if testing.current_sub_level == 2:
                testing.current_sub_level = 1
            else:
                testing.current_sub_level = 2
                testing.current_level -= 1
        testing.current_stage += 1
    if testing.current_stage <= testing.test.num_stages:
        testing.get_random_question()
        answers = db.session.query(Answers).\
            filter(Answers.question_id == testing.current_question.id).all()
        random.shuffle(answers)
    else:
        testing.current_question = None
        answers = None
    file = open(path, 'wb')
    pickle.dump(testing, file)
    file.close()
    return render_template('process_testing.html', testing=testing,
                           question=testing.current_question,
                           answers_for_question=answers)


if __name__ == "__main__":
    app.run(debug=False)
