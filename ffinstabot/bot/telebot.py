from typing import Pattern
from ffinstabot.bot.commands.login import *
from ffinstabot.bot.commands.help import *
from ffinstabot.bot.commands.logout import *
from ffinstabot.bot.commands.follow import *
from ffinstabot.bot.commands.unfollow import *
from ffinstabot.bot.commands.account import *
from ffinstabot.bot.commands.checknotifs import *
from ffinstabot.bot.commands.start import *
from ffinstabot.classes.callbacks import *


def setup(updater):
    dp = updater.dispatcher

    """ start_handler = ConversationHandler(
        entry_points=[CommandHandler('signin', client_sign_in), CallbackQueryHandler(client_sign_in, pattern=Callbacks.LOGIN)],
        states={
            LogInStates.INPUT_PHONE: [MessageHandler(Filters.text, input_phone)],
            LogInStates.INPUT_PASSWORD: [MessageHandler(Filters.text, input_password)],
            LogInStates.INPUT_CODE: [MessageHandler(Filters.text, input_code), CallbackQueryHandler(input_code, pattern=Callbacks.REQUEST_CODE)]
        },
        fallbacks=[CallbackQueryHandler(cancel_start)]
    )


    signout_handler = ConversationHandler(
        entry_points=[CommandHandler('signout', sign_out), CallbackQueryHandler(sign_out, pattern=Callbacks.LOGOUT)],
        states={
            LogOutStates.CONFIRM: [CallbackQueryHandler(confirm_sign_out, pattern=Callbacks.LOGOUT)]
        },
        fallbacks=[CallbackQueryHandler(cancel_sign_out)]
    )


    forwarder_handler = ConversationHandler(
        entry_points=[CommandHandler('forward', forward_message)],
        states = {
            ForwarderStates.MODE: [CallbackQueryHandler(forward_mode)],
            ForwarderStates.MESSAGE: [MessageHandler(Filters.text, select_message)],
            ForwarderStates.SELECT_SCRAPE: [CallbackQueryHandler(select_scrape)],
            ForwarderStates.SELECT_COUNT: [CallbackQueryHandler(select_count)],
            ForwarderStates.SELECT_GROUP: [CallbackQueryHandler(select_group)],
            ForwarderStates.CONFIRM: [CallbackQueryHandler(confirm)],
        },
        fallbacks=[CallbackQueryHandler(cancel_forward)]
    )


    scrape_handler = ConversationHandler(
        entry_points=[CommandHandler('scrape', scrape_followers)],
        states={
            ScrapeStates.SELECT_TARGET: [MessageHandler(Filters.text, select_target)],
            ScrapeStates.SELECT_NAME: [MessageHandler(Filters.text, select_name)],
            ScrapeStates.CONFIRM: [CallbackQueryHandler(confirm_scrape)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_scrape)
        ]
    )


    instagram_handler = ConversationHandler(
        entry_points=[CommandHandler('instagram', ig_login)],
        states={
            InstaStates.INPUT_USERNAME: [MessageHandler(Filters.text, instagram_username)],
            InstaStates.INPUT_PASSWORD: [MessageHandler(Filters.text, instagram_password)],
            InstaStates.INPUT_SECURITY_CODE: [MessageHandler(Filters.text, instagram_security_code)],
            InstaStates.INPUT_VERIFICATION_CODE: [MessageHandler(Filters.text, instagram_verification_code)],
        },
        fallbacks=[CallbackQueryHandler(cancel_instagram, pattern=Callbacks.CANCEL), CallbackQueryHandler(instagram_resend_scode, pattern=Callbacks.RESEND_CODE)]
    )

    
    unsubscribe_handler = ConversationHandler(
        entry_points=[CommandHandler('unsubscribe', unsubscribe_command)],
        states={
            UnsubscribeStates.CONFIRM: [CallbackQueryHandler(confirm_unsubscription)]
        },
        fallbacks=[]
    )

    # Commands
    dp.add_handler(CommandHandler("help", help_def))
    dp.add_handler(CommandHandler('adminhelp', admin_help))
    dp.add_handler(CommandHandler('account', check_account))
    dp.add_handler(CommandHandler('start', start_newsletter))
    dp.add_handler(CommandHandler('iglogout', instagram_log_out))
    dp.add_handler(CallbackQueryHandler(instagram_log_out, pattern=Callbacks.IGLOGOUT))
    dp.add_handler(instagram_handler)
    dp.add_handler(scrape_handler)
    dp.add_handler(signout_handler)
    dp.add_handler(start_handler)
    dp.add_handler(forwarder_handler)
    dp.add_handler(unsubscribe_handler)"""
    dp.add_error_handler(error)
