from datetime import timedelta, datetime
from os import remove, getenv
import pickle
import random

from flask import Flask, render_template, request, flash, session, \
    redirect, url_for, abort
from flask_login import LoginManager, login_user, login_required, \
    logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from UserLogin import UserLogin
from db_models import db, Users, Tests, Topics, Results, \
    TypeQuestions, Questions, Answers, DetailResults
from forms import LoginForm, RegisterForm
from test_process import Testing

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
db.init_app(app)
login_manager = LoginManager(app)


@app.errorhandler(401)
def pageNotAuthorized(error):
    return render_template('page_for_401.html')


@app.errorhandler(404)
def pageNotFound(error):
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


def best_results(results):
    list_mark, list_points = [], []
    for r in results:
        list_mark.append(r.mark)
        list_points.append(r.points)
    try:
        best_mark, best_points = max(list_mark), max(list_points)
    except:
        best_mark, best_points = None, None
    return best_mark, best_points


@app.route('/profile')
@login_required
def profile():
    user = current_user.user
    tests = db.session.query(Tests).all()
    user_results = db.session.query(Results) \
        .filter(Results.user_id == user.id).all()
    results = []
    for test in tests:
        test_results = [r for r in user_results if r.test_id == test.id]
        best_mark, best_points = best_results(test_results)
        results.append((test, best_mark, best_points))
    return render_template('profile.html', user=user, list_results=results)


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
            # авторизация пользователя в сессии
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
                    is_teacher = 2 if form.teacher.data else 1
                    psw_hash = generate_password_hash(form.psw.data)
                    user = Users(email=form.email.data, psw=psw_hash,
                                 name=form.name.data, role_id=is_teacher)
                    db.session.add(user)
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
        if not current_user.is_authenticated or current_user.user.role_id == 1:
            abort(401)
        title = 'Мои тесты'
        tests = db.session.query(Tests). \
            filter(Tests.author_id == current_user.user.id).all()
    else:
        try:
            int(topic_id)
        except:
            abort(404)
        topic = db.session.query(Topics).get_or_404(topic_id)
        tests = topic.tests_from_topic
        title = 'Тесты из ' + topic.name
    return render_template('tests_from_topic.html',
                           title=title, tests=tests)


@app.route('/test_preview_<test_id>')
@login_required
def test_preview(test_id):
    test = db.session.query(Tests).get_or_404(test_id)
    if current_user.user.role_id == 1:
        all_questions, student_results = None, None
        results = db.session.query(Results). \
            filter(Results.user_id == current_user.user.id,
                   Results.test_id == test_id). \
            order_by(Results.test_date.desc()).all()
        best_mark, best_points = best_results(results)
    else:
        best_mark, best_points, results = None, None, None
        all_questions = test.all_questions
        all_questions.sort(key=lambda x: x.difficulty_level)
        student_results = db.session.query(Users.name, Users.email,
                                           func.max(Results.mark),
                                           func.max(Results.points)) \
            .join(Users).filter(Results.test_id == test_id) \
            .group_by(Users.name, Users.email).all()
    return render_template('test_preview.html', best_points=best_points,
                           test=test, all_questions=all_questions,
                           best_mark=best_mark, results=results,
                           student_results=student_results)


@app.route('/create_test', methods=["POST", "GET"])
@login_required
def create_test():
    if current_user.user.role_id != 2:
        abort(401)
    if request.method == "GET":
        topic_names = db.session.query(Topics).order_by(Topics.name).all()
        return render_template('create_test.html', topics=topic_names)
    if request.method == 'POST':
        session.pop('_flashes', None)
        try:
            if db.session.query(Tests) \
                    .filter(Tests.name == request.form['name']).all():
                flash("Тест с таким названием уже существует", "error")
                return redirect(url_for('create_test'))
            else:
                if not len(request.form['new_topic']):
                    topic_id = int(request.form['topic'])
                    if topic_id == -1:
                        topic_id = None
                else:
                    exist_topic = db.session.query(Topics). \
                        filter(Topics.name == request.form['new_topic']).limit(1).all()
                    if exist_topic:
                        topic_id = exist_topic[0].id
                    else:
                        topic = Topics(name=request.form['new_topic'])
                        db.session.add(topic)
                        db.session.commit()
                        topic_id = topic.id
                test = Tests(name=request.form['name'], topic_id=topic_id,
                             description=request.form['description'],
                             author_id=current_user.user.id,
                             num_stages=request.form['num_stages'])
                db.session.add(test)
                db.session.commit()
                return redirect(url_for('create_questions', test_id=test.id))
        except:
            flash("Ошибка подключения к базе данных", "error")
            return redirect(url_for('create_test'))


@app.route('/create_questions_for_test_<test_id>', methods=["POST", "GET"])
@login_required
def create_questions(test_id):
    if current_user.user.role_id != 2 or current_user.user.id != \
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
                question = Questions(text=text_question, test_id=test_id,
                                     type_id=type_id, difficulty_level=lev)
                list_questions.append(question)
        db.session.add_all(list_questions)
        db.session.commit()
        return redirect(url_for('setting_answers', test_id=test_id))
    return render_template('create_questions.html', level_count=level_count,
                           test_id=test_id, types=types, list_keys=list_keys)


@app.route('/setting_answers_for_test_<test_id>', methods=["POST", "GET"])
@login_required
def setting_answers(test_id):
    if current_user.user.role_id != 2 or current_user.user.id != \
            db.session.query(Tests).get(test_id).author_of_test.id:
        abort(401)
    all_questions = db.session.query(Tests).get(test_id).all_questions
    if request.method == "POST":
        # словать вида id-question : count_answers
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
    if current_user.user.role_id != 2 or current_user.user.id != \
            db.session.query(Tests).get(test_id).author_of_test.id:
        abort(401)
    all_questions = db.session.query(Tests).get(test_id).all_questions
    answers = []
    for q in all_questions:
        for k in request.form.keys():
            if f'input_{q.id}' in k:
                (_, _, id_input_in_q) = k.rpartition('_')
                if q.type_id == 1:
                    corr = request.form[f"radio_{q.id}"] == \
                              f"{q.id}_{id_input_in_q}"
                elif q.type_id == 2:
                    corr = f"checkbox_{q.id}_{id_input_in_q}" in request.form
                answers.append(Answers(answer_text=request.form[k],
                                       question_id=q.id, correctness=corr))
    db.session.add_all(answers)
    db.session.commit()
    return redirect(url_for('test_preview', test_id=test_id))


@app.route('/additional_question_<test_id>', methods=["GET", "POST"])
@login_required
def additional_question(test_id):
    if request.method == "GET":
        test = db.session.query(Tests).get(test_id)
        types = db.session.query(TypeQuestions).all()
        return render_template('additional_question.html',
                               test_id=test_id, test=test, types=types)
    if request.method == "POST":
        text = request.form["text"]
        difficulty_level = request.form["difficulty_level"]
        type_id = request.form["type"]
        num_answers = request.form["num_answers"]
        question = Questions(text=text, test_id=test_id, type_id=type_id,
                             difficulty_level=difficulty_level)
        db.session.add(question)
        db.session.commit()
        return render_template('additional_answers.html', question=question,
                               test_id=test_id, num_answers=int(num_answers))


@app.route('/additional_answers_<test_id>/<question_id>', methods=["POST"])
@login_required
def additional_answers(test_id, question_id):
    if request.method == "POST":
        question = db.session.query(Questions).get(question_id)
        answers = []
        for k in request.form.keys():
            if 'input_' in k:
                (_, _, id_input) = k.rpartition('_')
                if question.type_id == 1:
                    correct = request.form["radio"] == f"{id_input}"
                elif question.type_id == 2:
                    correct = f"checkbox_{id_input}" in request.form
                answers.append(Answers(answer_text=request.form[k],
                                       question_id=question.id,
                                       correctness=correct))
        db.session.add_all(answers)
        db.session.commit()
        return redirect(url_for('test_preview', test_id=test_id))


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
        points = round(testing.points / testing.test.num_stages * 100, 2)
        if points <= 30:
            mark = 1
        elif 30 < points <= 60:
            mark = 2
        elif 60 < points <= 70:
            mark = 3
        elif 70 < points <= 85:
            mark = 4
        elif points > 85:
            mark = 5
        results = Results(user_id=current_user.user.id, test_id=int(test_id),
                          points=points, mark=testing.current_level,
                          test_date=datetime.now())
        db.session.add(results)
        db.session.commit()
        list_details = []
        for detail in testing.detail:
            d = DetailResults(question_id=detail[0].id, points=detail[1])
            list_details.append(d)
        results.details.extend(list_details)
        db.session.add(results)
        db.session.commit()
        remove(path)
        return redirect(url_for('test_preview', test_id=test_id))
    if request.method == "POST":
        res = 0
        if testing.current_question.type_id == 1:
            id_answer = int(request.form["radio_answer"])
            res = db.session.query(Answers).get(id_answer).correctness
            testing.points += float(res)
            testing.detail.append((testing.current_question, float(res)))
        elif testing.current_question.type_id == 2:
            true_vars, false_vars = 0, 0
            answers_for_question = db.session.query(Answers)\
                .filter(Answers.question_id == testing.current_question.id)\
                .all()
            count_correct = db.session.query(Answers). \
                filter(Answers.question_id == testing.current_question.id,
                       Answers.correctness).count()
            for answer in answers_for_question:
                if f'checkbox_{answer.id}' in request.form.keys():
                    res_ans = db.session.query(Answers). \
                        get(answer.id).correctness
                    if res_ans:
                        true_vars += 1
                    else:
                        false_vars += 1
            res = round(max(0, (true_vars - false_vars) / count_correct), 2)
            testing.points += res
            testing.detail.append((testing.current_question, res))
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
        answers = db.session.query(Answers). \
            filter(Answers.question_id == testing.current_question.id).all()
        random.shuffle(answers)
    else:
        testing.current_question, answers = None, None
    file = open(path, 'wb')
    pickle.dump(testing, file)
    file.close()
    return render_template('process_testing.html', testing=testing,
                           question=testing.current_question,
                           answers_for_question=answers)


if __name__ == "__main__":
    app.run(debug=True)
