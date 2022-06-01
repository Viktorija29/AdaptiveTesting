from db_models import Users


class UserLogin():
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