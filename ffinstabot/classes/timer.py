import time

class Timer():
    def __init__(self) -> None:
        self.start_time = None
        self.loop_time = None
        self.end_time = None

    def start_timer(self):
        self.start_time = time.time()

    def loop_timer(self) -> str or bool:
        self.loop_time = time.time()
        if not self.start_time:
            return False
        else:
            return '{:4.0f}'.format(self.loop_time - self.start_time)

    def end_timer(self) -> str or bool:
        self.end_time = time.time()
        if not self.start_time:
            return False
        else:
            self.start_time = None
            self.loop_time = None
            self.end_time = None
            return '{:4.0f}'.format(self.loop_time - self.start_time)