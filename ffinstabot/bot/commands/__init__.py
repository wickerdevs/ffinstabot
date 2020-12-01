from ffinstabot import applogger
from ffinstabot.bot import *
from ffinstabot.texts import *
from ffinstabot.classes.persistence import Persistence
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.followsession import FollowSession
from ffinstabot.classes.callbacks import *
from ffinstabot.classes.forwarder_markup import CreateMarkup, MarkupDivider
from ffinstabot.modules import instagram
from telegram import InputMediaPhoto, InputFile, Update
from telegram.ext import CallbackContext

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def send_photo(name, context, update):
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('{}.png'.format(name), 'rb'))


def check_auth(update, context):
    users_str = secrets.get_var('USERS')
    if isinstance(users_str, list):
        users = users_str
    else:
        users_str.replace('[', '')
        users_str.replace(']', '')
        users_str.replace(' ', '')
        users = users_str.split(',')
        for user, index in enumerate(users):
            users[index] = int(user)

    if int(update.effective_user.id) in users:
        applogger.debug('User is authorized to use the bot')
        return True
    else:
        applogger.debug('User is NOT authorized to use the bot.')
        try:
            context.bot.send_queued_message(text=not_authorized_text, chat_id=update.effective_user.id, parse_mode=ParseMode.MARKDOWN_V2)
            return False
        except Exception as error:
            applogger.debug('Error in sending message: {}'.format(error))
            return False
