from ffinstabot.modules import sheet
from ffinstabot.bot.commands import *

@send_typing_action
def unfollow_def(update:Update, context):
    if not check_auth(update, context):
        return ConversationHandler.END
    
    # Send options
    follows = sheet.get_follows(update.effective_chat.id)

    if follows is None:
        message = send_message(update, context, no_records_text)
        return ConversationHandler.END
    # Create Markup
    buttons = dict()
    for record in follows:
        buttons[record.target] = f'{record.target}\'s'
    buttons[Callbacks.CANCEL] = 'Cancel'
    markup = CreateMarkup(buttons).create_markup()
    # Initialize Persistence Obj
    session:FollowSession = FollowSession(update.effective_chat.id)
    # Send Message
    message = send_message(update, context, select_record_text, markup)
    session.set_message(message.message_id)
    return UnfollowStates.RECORD
    


@send_typing_action
def select_unfollow(update:Update, context):
    session:FollowSession = FollowSession.deserialize(Persistence.FOLLOW, update)
    if not session:
        update.callback_query.answer()
        return UnfollowStates.RECORD
    
    selected = update.callback_query.data
    if selected == Callbacks.CANCEL:
        return cancel_unfollow(update, context, session)

    session.set_target(selected)
    data = sheet.get_follow_data(session.user_id, session.target)
    
    if data is None:
        applogger.error(f'Error retrieving record info for id {session.user_id} and target {session.target}')
        send_message(update, context, error_retrieving_record_text)
        return ConversationHandler.END

    data = data[2].replace(' ', '')
    scraped = data.split(',')
    data = data[3].replace(' ', '')
    followed = data.split(',')
    session.set_scraped(scraped)
    session.set_followed(followed)

    # Send Confirmation Selection
    markup = CreateMarkup({Callbacks.CONFIRM: 'Confirm', Callbacks.CANCEL: 'Cancel'}).create_markup()
    send_message(update, context, confirm_unfollow_text.format(len(session.get_followed()), session.target), markup)
    return UnfollowStates.CONFIRM


@send_typing_action
def confirm_unfollow(update:Update, context):
    session:FollowSession = FollowSession.deserialize(Persistence.FOLLOW, update)
    if not session:
        update.callback_query.answer()
        return UnfollowStates.RECORD

    # Launch task
    send_message(update, context, launching_operation_text)
    instagram.enqueue_unfollow(session)
    session.discard()
    return ConversationHandler.END
    


@send_typing_action
def cancel_unfollow(update:Update, context, session:FollowSession=None):
    if not session:
        session = FollowSession.deserialize(Persistence.FOLLOW, update)
        if not session:
            return

    try:
        update.callback_query.edit_message_text(text=unfollow_cancelled_text)
    except:
        try:
            context.bot.edit_message_text(chat_id=session.user_id, message_id=session.message_id, text=unfollow_cancelled_text)
        except:
            message = send_message(update, context, unfollow_cancelled_text)
    session.discard()
    return ConversationHandler.END