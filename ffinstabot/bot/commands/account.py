from ffinstabot.bot.commands import *


@send_typing_action
def check_account(update, context):
    if not check_auth(update, context):
        return ConversationHandler.END
    instasession = InstaSession(update.effective_chat.id, update.effective_user.id)
    #message = send_message(update, context, message=checking_accounts_connection)
    try:
        if instasession.get_creds():
            # User logged into instagram
            text = connection_found_text.format(instasession.username, instasession.username)
            markup = CreateMarkup({Callbacks.LOGOUT: 'Log Out'}).create_markup()
            instasession.discard()
            message = send_message(update, context, text, markup)
        else:
            # User is not logged in
            markup = CreateMarkup({Callbacks.LOGIN: 'Log In'}).create_markup()
            instasession.discard()
            message = send_message(update, context, no_connection, markup)
    except:
        # Error
        instasession.discard()
        message = send_message(update, context, problem_connecting)
        context.bot.report_error('Error in Checking Instagram Connection')
        
