from ffinstabot.bot.commands import *


def help_def(update, context):
    update.message.delete()
    update.message.chat.send_message(text=help_text, parse_mode=ParseMode.HTML)