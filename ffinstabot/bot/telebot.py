from typing import Pattern

from telegram.message import Message
from ffinstabot.bot.commands.login import *
from ffinstabot.bot.commands.help import *
from ffinstabot.bot.commands.logout import *
from ffinstabot.bot.commands.follow import *
from ffinstabot.bot.commands.unfollow import *
from ffinstabot.bot.commands.account import *
from ffinstabot.bot.commands.checknotifs import *
from ffinstabot.bot.commands.start import *
from ffinstabot.bot.commands.incorrect import *
from ffinstabot.classes.callbacks import *


def setup(updater):
    dp:Dispatcher = updater.dispatcher

    instagram_handler = ConversationHandler(
        entry_points=[CommandHandler('login', ig_login), CallbackQueryHandler(ig_login, pattern=Callbacks.LOGIN, run_async=True)],
        states={
            InstaStates.INPUT_USERNAME: [MessageHandler(Filters.text, instagram_username, run_async=True)],
            InstaStates.INPUT_PASSWORD: [MessageHandler(Filters.text, instagram_password, run_async=True)],
            InstaStates.INPUT_SECURITY_CODE: [MessageHandler(Filters.text, instagram_security_code, run_async=True)],
        },
        fallbacks=[CallbackQueryHandler(cancel_instagram, pattern=Callbacks.CANCEL, run_async=True), CallbackQueryHandler(instagram_resend_scode, pattern=Callbacks.RESEND_CODE, run_async=True)]
    )


    follow_handler = ConversationHandler(
        entry_points=[CommandHandler('follow', follow_def, run_async=True)], 
        states={
            FollowStates.ACCOUNT: [MessageHandler(Filters.text, input_follow_account, run_async=True)],
            FollowStates.COUNT: [CallbackQueryHandler(input_follow_count, run_async=True)],
            FollowStates.CONFIRM : [CallbackQueryHandler(confirm_follow, pattern=Callbacks.CONFIRM, run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel_follow, pattern=Callbacks.CANCEL, run_async=True)]
    )


    unfollow_handler = ConversationHandler(
        entry_points=[CommandHandler('unfollow', unfollow_def, run_async=True)],
        states={
            UnfollowStates.RECORD: [CallbackQueryHandler(select_unfollow, run_async=True)],
            UnfollowStates.CONFIRM: [CallbackQueryHandler(confirm_unfollow, pattern=Callbacks.CONFIRM, run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel_unfollow, pattern=Callbacks.CANCEL, run_async=True)]
    )

    # Commands
    dp.add_handler(CommandHandler("help", help_def, run_async=True), )
    dp.add_handler(CommandHandler('account', check_account,  run_async=True))
    dp.add_handler(CommandHandler('logout', instagram_log_out, run_async=True))
    dp.add_handler(CallbackQueryHandler(instagram_log_out, pattern=Callbacks.LOGOUT, run_async=True))
    
    dp.add_handler(instagram_handler)
    dp.add_handler(follow_handler)
    dp.add_handler(unfollow_handler)
    dp.add_handler(MessageHandler(Filters.text, incorrect_command))
    dp.add_handler(MessageHandler(Filters.command, incorrect_command))

    dp.add_error_handler(error)
