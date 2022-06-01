from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# Пользователь
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    psw = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'),
                        default=1, nullable=False)

    created_tests = db.relationship('Tests', backref='author_of_test',
                                    cascade='all,delete-orphan')
    user_results = db.relationship('Results', backref='whose_result',
                                   cascade='all,delete-orphan')


# Роли пользователя
class Roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)

    users_with_role = db.relationship('Users', backref='role_of_user',
                                      cascade='all,delete-orphan')


# Тест
class Tests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    num_stages = db.Column(db.Integer, nullable=True)

    all_results_for_this_test = db.relationship('Results',
                                                backref='which_test_result',
                                                cascade='all,delete-orphan')
    all_questions = db.relationship('Questions', backref='which_test_question',
                                    cascade='all,delete-orphan')


# Тематический раздел, к которому принадлежит тест
class Topics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    tests_from_topic = db.relationship('Tests', backref='topic_of_test')


# Результаты тестов, пройденных пользователями
# Можно проходить тесты несколько раз и хранить результат для всех прохождений
class Results(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    mark = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    test_date = db.Column(db.DateTime, default=datetime.now)


# Вопросы
class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('type_questions.id'),
                        nullable=False)
    difficulty_level = db.Column(db.Integer, nullable=False)

    answers_for_question = db.relationship('Answers',
                                           backref='question_of_answer',
                                           cascade='all,delete-orphan')


# Тип вопроса (с 1 вариантом ответа, с несколькими, текстовый)
class TypeQuestions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    questions_with_type = db.relationship('Questions',
                                          backref='type_of_question',
                                          cascade='all,delete-orphan')


# Ответы
class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(500), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'),
                            nullable=False)
    correctness = db.Column(db.Boolean, nullable=False, default=False)
