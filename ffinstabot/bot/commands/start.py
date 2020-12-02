from ffinstabot.classes.settings import Settings
from ffinstabot.bot.commands import *


@send_typing_action
def start_def(update, context):
    if not check_auth(update, context):
        return ConversationHandler.END

    settings = sheet.get_settings(update.effective_chat.id)
    if settings:
        markup = CreateMarkup({Callbacks.EDIT_SETTINGS: 'Edit Settings'}).create_markup()
        send_message(update, context, startup_done, markup)
        return ConversationHandler.END
    
    settings = Settings(update.effective_chat.id)

    message = send_message(update, context, welcome)
    settings.set_message(message.message_id)
    return StartStates.TEXT


@send_typing_action
def input_text(update, context):
    settings:Settings = Settings.deserialize(Persistence.SETTINGS, update)
    if not settings:
        return

    settings.set_text(update.message.text)

    # TODO Change this part when implementing schedule queue --------------------|
    settings.set_frequency(timedelta(hours=6.0))
    settings.set_period(timedelta(days=365))
    settings.save()
    

    markup = CreateMarkup({Callbacks.LOGIN: 'Log In'}).create_markup()
    send_message(update, context, end, markup)

    settings.discard()
    return ConversationHandler.END
    # TODO -----------------------------------------------------------------------|


def input_frequency(update, context): #TODO
    pass


def input_period(update, context): # TODO
    pass

