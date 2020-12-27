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
        send_message(update, context, no_settings_found_text)
        return

    message_data = sheet.get_message(update.effective_chat.id)
    if message_data is not None:
        settings.set_message(message_data)
    # Check account connection
    instasession = InstaSession(update.effective_chat.id)
    if not instasession.get_creds():
        markup = CreateMarkup({Callbacks.ACCOUNT: 'My Accounts'}).create_markup()
        send_message(update, context, not_logged_in_text, markup)
        return
    # launch operation
    try: update.message.delete()
    except: pass
    instagram.enqueue_checknotifs(settings, instasession)
    settings.discard()
    instasession.discard()
    return

    