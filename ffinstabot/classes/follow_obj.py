from ffinstabot.classes.persistence import Persistence, persistence_decorator
import time


class Follow(Persistence):
    def __init__(self, user_id:int, message_id:int, account:str) -> None:
        super().__init__(Persistence.FOLLOW, user_id, message_id)
        self.account = account
        self.count = 0
        self.scraped = []
        self.followed = []
        self.failed = []
        self.unfollowed = []

    def __repr__(self) -> str:
        return f'Follow<{self.account}>'

    def get_account(self):
        return self.account

    def get_count(self):
        return self.count

    def get_scraped(self):
        return self.scraped.copy()

    def get_followed(self):
        return self.followed.copy()

    def get_failed(self):
        return self.failed.copy()

    def get_unfollowed(self):
        return self.unfollowed.copy()

    @persistence_decorator
    def set_count(self, count):
        self.count = count

    @persistence_decorator
    def set_scraped(self, scraped):
        self.scraped = scraped

    @persistence_decorator
    def set_followed(self, followed):
        self.followed = followed

    @persistence_decorator
    def set_failed(self, failed):
        self.failed = failed

    @persistence_decorator
    def set_unfollowed(self, unfollowed):
        self.unfollowed = unfollowed

    @persistence_decorator
    def add_followed(self, username):
        self.followed.append(username)

    @persistence_decorator
    def add_failed(self, failed):
        self.failed.append(failed)

    @persistence_decorator
    def add_unfollowed(self, username):
        self.unfollowed.append(username)

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
