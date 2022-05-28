from db_models import Users

#
# class UserLogin():
#     # потестить что будет, если пользователя нет в БД
#     def getUserFromDB(self, user_id, db):
#         self.user = db.session.query(Users).get(int(user_id))
#         return self
#
#     def create(self, user):
#         self.user = user
#         return self
#
#     def is_authenticated(self):
#         return True
#
#     def is_active(self):
#         return True
#
#     def is_anonymous(self):
#         return False
#
#     def get_id(self):
#         return str(self.user.id)


class UserLogin():
    # потестить что будет, если пользователя нет в БД
    # в user хранится объект класса db_models.Users
    def __init__(self, user_id, db):
        self.user = db.session.query(Users).get(int(user_id))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user.id)