from ffinstabot.bot.commands import *

@run_async
def help(update, context):
    update.message.delete()
    update.message.chat.send_message(text=help_text, parse_mode=ParseMode.HTML)