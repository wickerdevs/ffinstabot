from telegram import message
from ffinstabot.classes.settings import Settings
from ffinstabot.bot.commands import *

@send_typing_action
def checknotifs_def(update:Update, context:CallbackContext):
    if not check_auth(update, context):
        return

    # Get Settings
    settings = sheet.get_settings(update.effective_chat.id)
    if not settings:
        settings = Settings(update.effective_chat.id)
        settings.set_frequency(timedelta(hours=6.0))
        settings.set_text('Hi! Thank you for following me!')
        settings.set_period(timedelta(days=365))
        settings.save()
    message_data = sheet.get_message(update.effective_chat.id)
    if message_data is not None:
        settings.set_message(message_data)
    # Check account connection
    instasession = InstaSession(update.effective_chat.id)
    if not instasession.get_creds():
        send_message(update, context, not_logged_in_text)
        return
    # launch operation
    update.message.delete()
    instagram.enqueue_checknotifs(settings, instasession)
    settings.discard()
    instasession.discard()
    return

    