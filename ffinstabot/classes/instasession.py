from ffinstabot.classes.persistence import persistence_decorator
from ffinstabot.config import secrets
from ffinstabot.bot.commands import *
import os, redis

class InstaSession(Persistence):
    def __init__(self, user_id, message_id=None, method=Persistence.INSTASESSION):
        super().__init__(method, user_id, message_id=None)
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

    def set_session(self, session:str=None):
        if os.environ.get('PORT') in (None, ""):
            # Localhost
            secrets.set_var(f'instasession:{self.user_id}', self.username if session is None else session)
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))

            try:
                connector.delete('instasession:{}'.format(self.user_id))
            except:
                pass

            connector.set('instasession:{}'.format(self.user_id), self.username if session is None else session)
            connector.close()

    def get_session(self):
        if os.environ.get('PORT') in (None, ""):
            # Localhost
            session:str = secrets.get_var(f'instasession:{self.user_id}')
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            session:str = connector.get(f'instasession:{self.user_id}')
            connector.close()

        if not session:
            return None
        self.username = str(session)
        return str(session)

    def save_creds(self):
        """
        Store working instagram credentials (username and password)
        """
        creds = secrets.get_var('instacreds:{}'.format(self.user_id))
        if os.environ.get('PORT') in (None, ""):
            # Localhost
            if not creds:
                creds = dict()
            creds[self.username] = self.password
            secrets.set_var('instacreds:{}'.format(self.user_id), creds)
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            creds:dict = connector.hgetall('instacreds:{}'.format(self.user_id))
            if not creds:
                creds = dict()

            try:
                connector.delete('instacreds:{}'.format(self.user_id))
            except:
                pass

            creds[self.username] = self.password
            connector.hmset('instacreds:{}'.format(self.user_id), creds)
            connector.close()

    def get_creds(self):
        session = self.get_session()

        if os.environ.get('PORT') in (None, ""):
            creds = secrets.get_var('instacreds:{}'.format(self.user_id))
            if not creds:
                return False
            else:
                self.set_username(session if isinstance(session, str) else list(creds.keys())[0])

                if creds.get(self.username):
                    self.set_password(creds.get(self.username))
                    return True
                else:
                    return False
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            creds:dict = connector.hgetall('instacreds:{}'.format(self.user_id))
            connector.close()
            if not creds or list(creds.keys()) == []:
                # No credentials
                return False
            else:
                self.set_username(session if isinstance(session, str) else list(creds.keys())[0].decode('utf-8'))
                applogger.debug(self.username)
                if creds.get(bytes(self.username, encoding='utf8')):
                    self.set_password(creds.get(bytes(self.username, encoding='utf8')).decode('utf-8'))
                    return True
                else:
                    return False

    def delete_creds(self):
        session = self.get_session()
        self.username = None
        self.password = None

        if os.environ.get('PORT') in (None, ""):
            creds = secrets.get_var(f'instacreds:{self.user_id}')
            try: del creds[session]
            except: pass
            secrets.set_var('instacreds:{}'.format(self.user_id), creds)

            newsession = None
            for key in list(creds.keys()):
                if key != session:
                    
                    newsession = key
                    self.set_session(key)
                    self.set_username(key)
                    break
            applogger.debug(f'Set session: {newsession}')

            if not newsession:
                self.set_session(None)            
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            creds:dict = connector.hgetall('instacreds:{}'.format(self.user_id))
            try: del creds[bytes(session, encoding='utf8')]
            except: pass

            try:
                connector.delete('instacreds:{}'.format(self.user_id))
            except:
                pass

            connector.hmset('instacreds:{}'.format(self.user_id), creds)
            connector.close()

            newsession = None
            for key in list(creds.keys()):
                key = key.decode('utf-8')
                if key != session:
                    newsession = key
                    self.set_session(key)
                    self.set_username(key)
                    break

            if not newsession:
                self.set_session(None) 

    def get_all_creds(self):
        if os.environ.get('PORT') in (None, ""):
            creds = secrets.get_var('instacreds:{}'.format(self.user_id))
            if not creds:
                return None
            
            hascreds = False
            for cred in creds:
                if creds.get(cred):
                    hascreds = True
                    break
            if not hascreds: return None
            return creds
        else:
            connector = redis.from_url(os.environ.get('REDIS_URL'))
            creds:dict = connector.hgetall('instacreds:{}'.format(self.user_id))
            decoded = {}
            for key in creds:
                decoded[key.decode('utf-8')] = creds.get(key).decode('utf-8')

            hascreds = False
            for cred in decoded:
                if decoded.get(cred):
                    hascreds = True
                    break
            if not hascreds: return None
            return decoded
            



            