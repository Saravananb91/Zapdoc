import time

class Metrics:
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints = {}

    def mark(self, name):
        self.checkpoints[name] = time.time()

    def summary(self):
        return {
            k: round(v - self.start_time, 3)
            for k, v in self.checkpoints.items()
        }
