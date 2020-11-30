from instaclient.client.instaclient import InstaClient
from instaclient.errors.common import InvalidUserError, NotLoggedInError, PrivateAccountError
from ffinstabot.bot.commands import *

@send_typing_action
def follow_def(update, context):
    if check_auth(update, context):
        pass

    instasession:InstaSession = InstaSession(update.effective_user.id)
    update.message.delete()
    
    if instasession.get_creds():
        markup = CreateMarkup({'Cancel': Callbacks.CANCEL}).create_markup()
        message = update.effective_chat.send_message(chat_id=instasession.user_id, text=select_account_text, reply_markup=markup)
        instasession.set_message(message.message_id)
        return FollowStates.ACCOUNT

    else:
        # Not Logged In
        message = update.effective_chat.send_message(chat_id=instasession.user_id, text=not_logged_in_text, parse_mode=ParseMode.HTML)
        instasession.discard()
        return ConversationHandler.END


@send_typing_action
def input_follow_account(update, context):
    if check_auth(update, context):
        pass

    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION)
    follow:Follow = Follow(instasession.user_id, account=update.message.text.replace('@', ''))

    # Check Account
    try:
        instaclient = instagram.init_client()
        instaclient.is_valid_user(follow.account, discard_driver=True)
    except (InvalidUserError, PrivateAccountError):

        pass
    except NotLoggedInError:
        pass


