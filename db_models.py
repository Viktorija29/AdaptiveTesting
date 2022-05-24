from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#
# class Category(db.Model):
#     __tablename__ = 'categories'
#     id = db.Column(db.Integer(), primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     slug = db.Column(db.String(255), nullable=False)
#     created_on = db.Column(db.DateTime(), default=datetime.now)
#     posts = db.relationship('Post', backref='category', cascade='all,delete-orphan')
#
#     def __repr__(self):
#         return "<{}:{}>".format(self.id, self.name)
#
#
# post_tags = db.Table('post_tags',
#     db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
#     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
# )
#
#
# class Post(db.Model):
#     __tablename__ = 'posts'
#     id = db.Column(db.Integer(), primary_key=True)
#     title = db.Column(db.String(255), nullable=False)
#     slug = db.Column(db.String(255), nullable=False)
#     content = db.Column(db.Text(), nullable=False)
#     created_on = db.Column(db.DateTime(), default=datetime.now)
#     updated_on = db.Column(db.DateTime(), default=datetime.now, onupdate=datetime.now)
#     category_id = db.Column(db.Integer(), db.ForeignKey('categories.id'))
#
#     def __repr__(self):
#         return "<{}:{}>".format(self.id, self.title[:10])
#
#
# class Tag(db.Model):
#     __tablename__ = 'tags'
#     id = db.Column(db.Integer(), primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     slug = db.Column(db.String(255), nullable=False)
#     created_on = db.Column(db.DateTime(), default=datetime.now)
#     posts = db.relationship('Post', secondary=post_tags, backref='tags')
#
#     def __repr__(self):
#         return "<{}:{}>".format(self.id, self.name)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    psw = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"profiles {self.id}"

