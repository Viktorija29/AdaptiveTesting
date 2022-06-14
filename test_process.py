import random


class Testing:
    def __init__(self, test):
        self.test = test
        self.questions_by_levels = \
            dict.fromkeys([x for x in range(1, test.num_stages + 1)], [])
        for q in test.all_questions:
            self.questions_by_levels[q.difficulty_level] = \
                self.questions_by_levels[q.difficulty_level] + [q]
        for k in self.questions_by_levels.keys():
            buf = self.questions_by_levels[k].copy()
            random.shuffle(buf)
            self.questions_by_levels[k] = buf
        self.current_stage = 1
        self.current_level = int((test.num_stages + 1) / 2) \
            if test.num_stages % 2 \
            else int(test.num_stages / 2)
        self.current_sub_level = 1 if test.num_stages % 2 else 2
        self.points = 0
        self.current_question = None
        self.detail = []

    def get_random_question(self):
        buf = self.questions_by_levels[self.current_level]
        if len(buf) > 1:
            q = buf[0]
            buf = buf[1:]
        elif len(buf) == 1:
            q = buf[0]
            buf = []
        self.questions_by_levels[self.current_level] = buf
        self.current_question = q
