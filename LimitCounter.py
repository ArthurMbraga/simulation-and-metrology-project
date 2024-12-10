class LimitCounter:
    def __init__(self, limit):
        self.limit = limit
        self.counter = 0

    def incrementAndCheck(self):
        self.counter += 1

        if self.counter >= self.limit:
            self.counter = 0
            return True
        return False
