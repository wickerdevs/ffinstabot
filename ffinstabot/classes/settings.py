from datetime import timedelta
from ffinstabot.classes.setting import Setting
from ffinstabot.classes.timer import Timer
import jsonpickle, json
from ffinstabot.classes.persistence import Persistence, persistence_decorator
from ffinstabot.modules import sheet
import datetime

class Settings(Persistence, Timer):
    def __init__(self, user_id:int, message_id:int=None) -> None:
        super().__init__(Persistence.SETTINGS, user_id, message_id)
        super(Timer, self).__init__()
        self.settings = {} # username: setting

    def __repr__(self) -> str:
        return jsonpickle.encode(self)

    def __str__(self) -> str:
        return f'Settings<{self.user_id}>'
        
    def from_string(string:str):
        return jsonpickle.decode(string)

    def get_setting(self, account:str):
        try:
            setting:Setting = self.settings.get(account)
            if setting:
                return setting
            return None
        except:
            return None

    @persistence_decorator
    def set_setting(self, account:str, setting:Setting=None):
        if setting:
            self.settings[account] = setting
            return setting
        else:
            setting = Setting(account)
            self.settings[account] = setting
            return setting

    @persistence_decorator
    def set_text(self, account:str, text:str):
        setting = self.settings.get(account)
        if not setting:
            return False
        setting.set_text(text)
        self.settings[account] = setting
        return True

    @persistence_decorator
    def set_frequency(self, account:str, frequency:timedelta):
        setting = self.settings.get(account)
        if not setting:
            return False
        setting.set_frequency(frequency)
        self.settings[account] = setting
        return True

    @persistence_decorator
    def set_period(self, account:str, period:timedelta):
        setting = self.settings.get(account)
        if not setting:
            return False
        setting.set_period(period)
        self.settings[account] = setting
        return True

    def save(self):
        sheet.set_settings(self)