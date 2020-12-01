import os, logging
import telegram
from ffinstabot import updater, BOT_TOKEN, URL, PORT, LOCALHOST, applogger


if __name__ == '__main__':
    if LOCALHOST:
        applogger.info('Polling Telegram bot...')
        updater.start_polling()
    else:
        # Setup Telegram Webhook
        applogger.debug('STARTING WEBHOOK')
        updater.start_webhook(listen="0.0.0.0",
                            port=PORT,
                            url_path=BOT_TOKEN)
        applogger.debug('WEBHOOK STARTED - SETTING UP WEBHOOK')
        updater.bot.set_webhook('{URL}/{HOOK}'.format(URL=URL, HOOK=BOT_TOKEN))
        applogger.debug('WEBHOOK SET UP CORRECTLY')
        updater.idle()
