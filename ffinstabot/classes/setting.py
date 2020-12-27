from datetime import timedelta


class Setting(object):
    def __init__(self, account:str=None, text:str=None, frequency:timedelta=None, period:timedelta=None) -> None:
        self.account = account
        self.text = text
        self.frequency = frequency
        self.period = period

    def set_account(self, account:str):
        self.account = account

    def set_text(self, text:str):
        self.text = text

    def set_frequency(self, frequency:timedelta):
        self.frequency = frequency

    def set_period(self, period:timedelta):
        self.period = period

    def get_account(self):
        return self.account

    def get_text(self):
        return self.text

    def get_frequency(self):
        return self.frequency

    def get_period(self):
        return self.period