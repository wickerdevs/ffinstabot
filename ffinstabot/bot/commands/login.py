from instaclient.errors.common import InstaClientError, InvaildPasswordError, InvalidSecurityCodeError, InvalidUserError, NotLoggedInError, PrivateAccountError, InvalidVerificationCodeError, VerificationCodeNecessary, SuspisciousLoginAttemptError
from instaclient.client.instaclient import InstaClient
from telegram.ext import updater
from ffinstabot.bot.commands import *
from ffinstabot.bot.commands.checknotifs import *
from ffinstabot import applogger

client:InstaClient


@send_typing_action
def ig_login(update, context):
    if not check_auth(update, context):
        return ConversationHandler.END

    # Check IG status    
    instasession:InstaSession = InstaSession(update.effective_chat.id, update.effective_user.id)
    markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
    message = send_message(update, context, checking_ig_status)
    instasession.set_message(message.message_id)
    result = instasession.get_creds()
    if result:
        # Account is already logged in
        applogger.debug('Account already logged in')
        context.bot.edit_message_text(text=user_logged_in_text, chat_id=instasession.user_id, message_id=message.message_id)
        instasession.discard()
        return ConversationHandler.END

    else:
        # Check if account is already registered
        # Request Username
        context.bot.edit_message_text(text=input_ig_username_text, chat_id=instasession.user_id, message_id=message.message_id, reply_markup=markup)
        return InstaStates.INPUT_USERNAME

    

@send_typing_action
def instagram_username(update, context):
    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION, update)
    if not instasession:
        return InstaStates.INPUT_USERNAME
    
    username = update.message.text 
    message = send_message(update, context, checking_user_vadility_text)
    instasession.set_message(message.message_id)
    markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
    # Verify User
    try:
        instaclient = instagram.init_client()
        result = instaclient.is_valid_user(username, discard_driver=True)
        applogger.debug('USER {} IS VALID: {}'.format(username, result))
    except InvalidUserError as error:
        context.bot.edit_message_text(text=invalid_user_text.format(error.username), chat_id=update.effective_chat.id, message_id=instasession.message_id, reply_markup=markup)
        instasession.set_message(message.message_id)
        return InstaStates.INPUT_USERNAME
    except (PrivateAccountError, NotLoggedInError) as error:
        pass
    instasession.set_username(username)
    # Request Password
    context.bot.edit_message_text(text=input_password_text, chat_id=update.effective_chat.id, message_id=instasession.message_id, reply_markup=markup)
    return InstaStates.INPUT_PASSWORD



@send_typing_action
def instagram_password(update, context):
    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION, update)
    if not instasession:
        return InstaStates.INPUT_PASSWORD

    markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
    password = update.message.text
    instasession.set_password(password)
    message = send_message(update, context, attempting_login_text)
    instasession.set_message(message.message_id)

    if len(password) < 6:
        context.bot.edit_message_text(text=invalid_password_text.format(instasession.password), chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        return InstaStates.INPUT_PASSWORD
        
    # Attempt login
    instaclient = instagram.init_client()
    try:
        instaclient.login(instasession.username, instasession.password)
    except InvalidUserError as error:
        context.bot.edit_message_text(text=invalid_user_text.format(error.username), chat_id=update.effective_chat.id, message_id=instasession.message_id, reply_markup=markup)
        instasession.set_message(message.message_id)
        instaclient.discard_driver()
        return InstaStates.INPUT_USERNAME

    except InvaildPasswordError:
        context.bot.edit_message_text(text=invalid_password_text.format(instasession.password), chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        instaclient.discard_driver()
        return InstaStates.INPUT_PASSWORD
        
    except VerificationCodeNecessary:
        context.bot.edit_message_text(text=verification_code_necessary, chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        instaclient.discard_driver()
        return ConversationHandler.END

    except SuspisciousLoginAttemptError as error:
        # Creds are correct
        instaclient.driver.save_screenshot('suspicious_login_attempt.png')
        context.bot.report_error(error, send_screenshot=True, screenshot_name='suspicious_login_attempt')
        if os.path.exists("suspicious_login_attempt.png"):
            os.remove("suspicious_login_attempt.png")
        instasession.increment_code_request()
        if error.mode == SuspisciousLoginAttemptError.PHONE:
            text = input_security_code_text
        else:
            text = input_security_code_text_email
        markup = CreateMarkup({Callbacks.RESEND_CODE: 'Resend Code', Callbacks.CANCEL: 'Cancel'}).create_markup()
        context.bot.edit_message_text(text=text, chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        global client
        client = instaclient
        return InstaStates.INPUT_SECURITY_CODE

    # Login Successful
    instasession.save_creds()
    context.bot.edit_message_text(text=login_successful_text, chat_id=instasession.user_id, message_id=instasession.message_id)
    instasession.discard()
    instaclient.discard_driver()
    settings:Settings = sheet.get_settings(instasession.user_id)
    settings.account = instasession.username
    sheet.set_settings(settings)
    checknotifs_def(update, context)
    return ConversationHandler.END


@send_typing_action
def instagram_resend_scode(update, context):
    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION, update)
    if not instasession:
        return InstaStates.INPUT_SECURITY_CODE

    try:
        global client
        client.resend_security_code()
        text = 'phone number'
    except SuspisciousLoginAttemptError as error:
        if error.mode == SuspisciousLoginAttemptError.EMAIL:
            # Code to sent via email
            text = 'email'
        else:
            text = 'phone number'
    instasession.increment_code_request()
    update.callback_query.answer()
    markup = CreateMarkup({Callbacks.RESEND_CODE: 'Resend Code', Callbacks.CANCEL: 'Cancel'}).create_markup()
    context.bot.edit_message_text(text=security_code_resent.format(text, instasession.code_request), chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
    return InstaStates.INPUT_SECURITY_CODE
    

""" 
@send_typing_action
def instagram_verification_code(update, context):
    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION, update)
    if not instasession:
        return InstaStates.INPUT_VERIFICATION_CODE

    markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
    code = update.message.text
    message = update.effective_chat.send_message(text=validating_code_text, reply_markup=markup)
    instasession.set_scode(code)
    instasession.set_message(message.message_id)

    try:
        instaclient.input_verification_code(code)
    except InvalidVerificationCodeError:
        context.bot.edit_message_text(text=invalid_security_code_text.format(code), chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        return InstaStates.INPUT_VERIFICATION_CODE

    # Login Successful
    instasession.save_creds()
    context.bot.edit_message_text(text=login_successful_text, chat_id=instasession.user_id, message_id=instasession.message_id)
    instasession.discard()
    return ConversationHandler.END """



@send_typing_action
def instagram_security_code(update, context):
    instasession:InstaSession = InstaSession.deserialize(Persistence.INSTASESSION, update)
    if not instasession:
        return InstaStates.INPUT_SECURITY_CODE

    markup = CreateMarkup({Callbacks.CANCEL: 'Cancel'}).create_markup()
    code = update.message.text
    message = send_message(update, context, validating_code_text, markup)
    instasession.set_scode(code)
    instasession.set_message(message.message_id)

    try:
        global client
        client.input_security_code(code)
    except InvalidSecurityCodeError:
        context.bot.edit_message_text(text=invalid_security_code_text.format(code), chat_id=instasession.user_id, message_id=instasession.message_id, reply_markup=markup)
        return InstaStates.INPUT_SECURITY_CODE

    # Login Successful
    instasession.save_creds()
    context.bot.edit_message_text(text=login_successful_text, chat_id=instasession.user_id, message_id=instasession.message_id)
    instasession.discard()
    client.discard_driver()
    checknotifs_def(update, context)
    return ConversationHandler.END



@send_typing_action
def cancel_instagram(update, context, instasession:InstaSession=None):
    if not instasession:
        instasession = InstaSession.deserialize(Persistence.INSTASESSION, update)
        if not instasession:
            return
    try:
        update.callback_query.edit_message_text(text=cancelled_instagram_text)
    except:
        try:
            context.bot.edit_message_text(chat_id=instasession.user_id, message_id=instasession.message_id, text=cancelled_instagram_text)
        except:
            message = send_message(update, context, cancelled_instagram_text)
    instasession.discard()
    try: client.discard_driver()
    except: pass
    return ConversationHandler.END

    
    






