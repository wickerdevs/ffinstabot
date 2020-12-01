from telegram import message
from ffinstabot.classes.settings import Settings
from ffinstabot.bot.commands import *

@send_typing_action
def settings_def(update:Update, context):
    if not check_auth(update, context):
        return ConversationHandler.END

    if update.callback_query:
        message_id = update.callback_query.inline_message_id
    else:
        message_id = update.message.message_id

    # Get Settings
    settings = sheet.get_settings(update.effective_user.id)
    if not settings:
        settings = Settings(update.effective_chat.id)
        settings.set_frequency(timedelta(hours=6.0))
        settings.set_text('Hi! Thank you for following me!')
        settings.set_period(timedelta(days=365))
        settings.save()
    settings.set_message(message_id)

    # Create Marup & Send Message
    markup = CreateMarkup({
        SettingsStates.TEXT: 'Default Text',
        SettingsStates.CANCEL: 'Cancel'
    }).create_markup()
    # TODO Add the rest of the settings to the markup
    send_message(update, context, select_setting_text, markup)
    return SettingsStates.SELECT


@send_typing_action
def select_setting(update, context):
    settings = Settings.deserialize(Persistence.SETTINGS, update)
    if not settings:
        return 

    data = int(update.callback_query.data)
    if data == SettingsStates.CANCEL:
        return cancel_settings(update, context, settings)
    elif data == SettingsStates.FREQUENCY:
        text = select_frequency_text
        markup = CreateMarkup({}) # TODO
    elif data == SettingsStates.PERIOD:
        text = select_period_text
        markup = CreateMarkup({}) # TODO
    else:
        text = select_text_text
        markup = CreateMarkup({SettingsStates.CANCEL: 'Cancel'}).create_markup()

    message = send_message(update, context, text, markup)
    settings.set_message(message.message_id)
    return data


@send_typing_action
def select_frequency(update, context):
    pass


@send_typing_action
def select_period(update, context):
    pass


@send_typing_action
def select_text(update, context):
    settings:Settings = Settings.deserialize(Persistence.SETTINGS, update)
    if not settings:
        return 

    text = update.message.text
    settings.set_text(text)
    settings.save()

    markup = CreateMarkup({Callbacks.EDIT_SETTINGS: 'Edit Settings'}).create_markup()
    send_message(update, context, edited_text_text, markup)
    settings.discard()
    return ConversationHandler.END


@send_typing_action
def cancel_settings(update, context, settings:Settings=None):
    if not settings:
        settings = FollowSession.deserialize(Persistence.FOLLOW, update)
        if not settings:
            return

    send_message(update, context, cancelled_editing_settings)
    settings.discard()
    return ConversationHandler.END
