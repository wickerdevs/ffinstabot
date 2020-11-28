from ffinstabot.classes.persistence import Persistence, persistence_decorator
from ffinstabot.modules import sheet
import datetime

class Settings(Persistence):
    def __init__(self, user_id:int, message_id:int=None, text:str=None, frequency:datetime.timedelta=None, account:str=None) -> None:
        super().__init__(Persistence.SETTINGS, user_id, message_id)
        self.text = text
        self.frequency = frequency
        self.account = account

    @persistence_decorator
    def set_text(self, text:str):
        self.text = text

    @persistence_decorator
    def set_schedule(self, frequency:datetime.timedelta):
        self.frequency = frequency

    @persistence_decorator
    def set_account(self, account):
        self.account = account

    def save(self):
        sheet.set_settings(self)