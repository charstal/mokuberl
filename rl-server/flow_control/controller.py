import datetime


class FlowController:
    # lecky bucket
    def __init__(self, capacity=20, rate=3):
        self.capacity = capacity
        self.last_time = datetime.datetime.now()
        self.water = 0
        self.rate = rate

    def grant(self):
        now = datetime.datetime.now()

        self.water = max(
            0, self.water - (now-self.last_time).seconds * self.rate)

        self.last_time = now
        if ((self.water + 1) < self.capacity):
            self.water += 1
            return True
        else:
            return False


if __name__ == "__main__":
    fc = FlowController(size=30)
