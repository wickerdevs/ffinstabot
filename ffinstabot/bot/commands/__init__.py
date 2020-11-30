from ffinstabot.bot import *
from ffinstabot.texts import *
from ffinstabot.classes.persistence import Persistence
from ffinstabot.classes.instasession import InstaSession
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
    if str(update.effective_user.id) in secrets.get_var('USERS'):
        print('User is authorized to use the bot')
        return True
    else:
        print('User is NOT authorized to use the bot.')
        try:
            context.bot.send_queued_message(text=not_authorized_text, chat_id=update.effective_user.id, parse_mode=ParseMode.MARKDOWN_V2)
            return False
        except Exception as error:
            print('Error in sending message: ', error)
            return False
