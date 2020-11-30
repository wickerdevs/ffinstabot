from ffinstabot.classes.persistence import persistence_decorator
from ffinstabot.config import secrets
from ffinstabot.bot.commands import *
import os, redis

class InstaSession(Persistence):
    def __init__(self, user_id, message_id=None):
        super().__init__(Persistence.INSTASESSION, user_id, message_id=None)
        self.username = None
        self.password = None
        self.security_code = None
        self.code_request = 0

    @persistence_decorator
    def set_username(self, username):
        self.username = username

    @persistence_decorator
    def set_password(self, password):
        self.password = password

    @persistence_decorator
    def set_scode(self, scode):
        self.security_code = scode

    @persistence_decorator
    def increment_code_request(self):
        self.code_request += 1

    def save_creds(self):
        """
        Store working instagram credentials (username and password)
        """
        if os.environ.get('PORT') in (None, ""):
            # Localhost
            secrets.set_var('instacreds:{}'.format(self.user_id), {self.username: self.password})
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            try:
                connector.delete('instacreds:{}'.format(self.user_id))
            except:
                pass
            connector.hmset('instacreds:{}'.format(self.user_id), {self.username: self.password})
            connector.close()

    def get_creds(self):
        if os.environ.get('PORT') in (None, ""):
            creds = secrets.get_var('instacreds:{}'.format(self.user_id))
            if not creds:
                return False
            else:
                self.set_username(list(creds.keys())[0])
                self.set_password(creds.get(self.username))
                return True
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            creds:dict = connector.hgetall('instacreds:{}'.format(self.user_id))
            connector.close()
            if not creds or list(creds.keys()) == []:
                # No credentials
                return False
            else:
                self.set_username(list(creds.keys())[0].decode('utf-8'))
                print(self.username)
                self.set_password(creds.get(bytes(self.username, encoding='utf8')).decode('utf-8'))
                return True

    def delete_creds(self):
        if os.environ.get('PORT') in (None, ""):
            secrets.set_var('instacreds:{}'.format(self.user_id), None)
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            try:
                connector.delete('instacreds:{}'.format(self.user_id))
            except:
                pass
