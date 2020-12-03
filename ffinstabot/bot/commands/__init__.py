from ffinstabot import applogger
from ffinstabot.bot import *
from ffinstabot.texts import *
from ffinstabot.classes.persistence import Persistence
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.followsession import FollowSession
from ffinstabot.classes.callbacks import *
from ffinstabot.classes.forwarder_markup import CreateMarkup, MarkupDivider
from ffinstabot.modules import instagram, sheet
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


def send_message(update:Update, context:CallbackContext, message:str, markup=None):
    if update.callback_query:
        if markup:
            message = update.callback_query.edit_message_text(text=message, reply_markup=markup)
        else:
            message = update.callback_query.edit_message_text(text=message)
        sheet.set_message(update.effective_user.id, message.message_id)
        return message

    elif sheet.get_message(update.effective_chat.id):
        message_id = sheet.get_message(update.effective_chat.id)
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
            applogger.debug(f'Deleted bot message. id: {message_id}')
        except: pass

    try: 
        message_id = update.message.message_id
        update.message.delete()
        applogger.debug(f'Deleted user message. id: {message_id}')
    except: pass

    if markup:
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        message = context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)

    sheet.set_message(update.effective_user.id, message.message_id)
    return message


def check_auth(update, context):
    users_str = secrets.get_var('USERS')
    if isinstance(users_str, str):
        users_str = users_str.replace('[', '')
        users_str = users_str.replace(']', '')
        users_str = users_str.replace(' ', '')
        users_str = users = users_str.split(',')
        for index, user in enumerate(users):
            users[index] = int(user)
    else:
        users = users_str

    if int(update.effective_user.id) in users:
        applogger.debug('User is authorized to use the bot')
        return True
    else:
        applogger.debug('User is NOT authorized to use the bot.')
        try:
            send_message(update, context, not_authorized_text)
            return False
        except Exception as error:
            applogger.debug('Error in sending message: {}'.format(error))
            return False
