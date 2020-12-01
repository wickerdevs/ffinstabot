from instaclient.client.instaclient import InstaClient
from instaclient.errors.common import InvalidUserError, NotLoggedInError, PrivateAccountError
from ffinstabot.bot.commands import *

@send_typing_action
def follow_def(update, context):
    if not check_auth(update, context):
        return ConversationHandler.END

    session:FollowSession = FollowSession(update.effective_user.id)
    
    if session.get_creds():
        markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
        message = send_message(update, context, select_account_text, markup)
        session.set_message(message.message_id)
        return FollowStates.ACCOUNT

    else:
        # Not Logged In
        message = send_message(update, context, not_logged_in_text)
        session.discard()
        return ConversationHandler.END


@send_typing_action
def input_follow_account(update, context):
    if not check_auth(update, context):
        return

    session:FollowSession = FollowSession.deserialize(Persistence.FOLLOW, update)
    session.set_target(update.message.text.replace('@', ''))
    update.message.delete()
    context.bot.edit_message_text(text=checking_user_vadility_text, chat_id=session.user_id, message_id=session.message_id, parse_mode=ParseMode.HTML)
    # Check Account
    try:
        instaclient = instagram.init_client()
        instaclient.is_valid_user(session.target, discard_driver=True)
    except (InvalidUserError, PrivateAccountError):
        markup = CreateMarkup({'Cancel': Callbacks.CANCEL}).create_markup()
        context.bot.edit_message_text(text=error_when_checking_account.format(session.target), chat_id=session.user_id, message_id=session.message_id, parse_mode=ParseMode.HTML, reply_markup=markup)
        return FollowStates.ACCOUNT
    except NotLoggedInError:
        pass

    # Select Count
    markup = CreateMarkup({
        Callbacks.TEN: '10',
        Callbacks.TFIVE: '25',
        Callbacks.FIFTY: '50',
        Callbacks.SFIVE: '75',
        Callbacks.CANCEL: 'Cancel'
    }, cols=2).create_markup()
    context.bot.edit_message_text(text=select_count_text, chat_id=session.user_id, message_id=session.message_id, parse_mode=ParseMode.HTML, reply_markup=markup)
    return FollowStates.COUNT


@send_typing_action
def input_follow_count(update, context):
    if not check_auth(update, context):
        return

    session:FollowSession = FollowSession.deserialize(Persistence.FOLLOW, update)
    if update.callback_query.data == Callbacks.CANCEL:
        return cancel_follow(update, context, session)

    session.set_count(int(update.callback_query.data))
    
    # Confirm
    markup = CreateMarkup({
        Callbacks.CONFIRM: 'Confirm',
        Callbacks.CANCEL: 'Cancel' 
    }).create_markup()
    context.bot.edit_message_text(text=confirm_follow_text.format(session.count, session.target), chat_id=session.user_id, message_id=session.message_id, parse_mode=ParseMode.HTML, reply_markup=markup)
    return FollowStates.CONFIRM


@send_typing_action
def confirm_follow(update, context):
    if not check_auth(update, context):
        return

    session:FollowSession = FollowSession.deserialize(Persistence.FOLLOW, update)
    context.bot.edit_message_text(text=launching_operation_text, chat_id=session.user_id, message_id=session.message_id, parse_mode=ParseMode.HTML)
    instagram.enqueue_follow(session)
    session.discard()
    return ConversationHandler.END
    

@send_typing_action
def cancel_follow(update, context, session:FollowSession=None):
    if not session:
        session = FollowSession.deserialize(Persistence.FOLLOW, update)
        if not session:
            return

    try:
        update.callback_query.edit_message_text(text=follow_cancelled_text)
    except:
        try:
            context.bot.edit_message_text(chat_id=session.user_id, message_id=session.message_id, text=follow_cancelled_text)
        except:
            message = send_message(update, context, follow_cancelled_text)
    session.discard()
    return ConversationHandler.END

                                                                                                                                                                                                                               


