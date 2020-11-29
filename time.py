from datetime import datetime, timedelta
import json
from typing import Set
import jsonpickle
from ffinstabot.classes.settings import Settings

print('Date')
date = datetime.utcnow()
print(date.__str__())
print(date.isoformat())

print('\nDuration')
duration = timedelta(hours=6.0)
period = timedelta(days=30)
print(duration.__str__())
print(period.__str__())

print('\nJson Pickle')

settings = Settings(1234, 54321)
settings.set_account('davidwickerhf')
settings.set_message('message_id_4234234')
settings.set_period(period)
settings.set_frequency(duration)
settings.set_text('Default Text')

string = repr(settings)
print('STRING: ', string)

obj = Settings.from_string(string)
print('OBJECT: ', obj)
type(obj)
