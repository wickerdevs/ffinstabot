from ffinstabot.bot.commands import *


@send_typing_action
@run_async
def check_account(update, context):
    if not check_auth(update, context):
        return
    instasession = InstaSession(update.effective_chat.id, update.effective_user.id)
    update.message.delete()
    message = update.effective_chat.send_message(text=checking_accounts_connection)
    try:
        if instasession.get_creds():
            # User logged into instagram as well
            text += '\n\n' + ig_account_info.format(instasession.username, instasession.username)
            markup = CreateMarkup({Callbacks.LOGOUT: 'Log Out'}).create_markup()
            manager.discard()
            instasession.discard()
            context.bot.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML, chat_id=update.effective_chat.id, message_id=message.message_id)
        else:
            # User is not logged in
            markup = CreateMarkup({Callbacks.LOGIN: 'Log In'}).create_markup()
            manager.discard()
            instasession.discard()
            context.bot.edit_message_text(no_connection, reply_markup=markup, parse_mode=ParseMode.HTML, chat_id=update.effective_chat.id, message_id=message.message_id)
    except:
        # Error
        manager.discard()
        instasession.discard()
        context.bot.edit_message_text(problem_connecting, parse_mode=ParseMode.HTML, chat_id=update.effective_chat.id, message_id=message.message_id)
        
