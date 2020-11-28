from datetime import timedelta
import json

import jsonpickle
from ffinstabot.classes.persistence import Persistence, persistence_decorator
from ffinstabot.modules import sheet
import datetime

class Settings(Persistence):
    def __init__(self, user_id:int, message_id:int=None) -> None:
        super().__init__(Persistence.SETTINGS, user_id, message_id)
        self.text = None
        self.frequency = None
        self.account = None
        self.period = None

    def __repr__(self) -> str:
        return jsonpickle.encode(self)

    def __str__(self) -> str:
        return f'Settings<{self.user_id}>'
        
    def from_string(string:str):
        return jsonpickle.decode(string)

    @persistence_decorator
    def set_text(self, text:str):
        self.text = text

    @persistence_decorator
    def set_frequency(self, frequency:datetime.timedelta):
        self.frequency = frequency

    @persistence_decorator
    def set_account(self, account):
        self.account = account

    @persistence_decorator
    def set_period(self, period:timedelta):
        self.period = period

    def save(self):
        sheet.set_settings(self)