import os, logging
from rq import Queue
from worker import conn
from instaclient import InstaClient
from telegram.ext.updater import Updater
from telegram.ext.defaults import Defaults
from telegram.utils.request import Request
from ffinstabot.classes.mq_bot import MQBot
from telegram import ParseMode
from telegram.ext import messagequeue as mq

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger('FFInstaBot')


def instaclient_error_callback(driver):
    from ffinstabot import telegram_bot as bot
    driver.save_screenshot('error.png')
    bot.report_error('instaclient.__find_element() error.', send_screenshot=True, screenshot_name='error')
    os.remove('error.png')


LOCALHOST = True
queue = None
if os.environ.get('PORT') not in (None, ""):
    # Code running locally
    LOCALHOST = False
    queue = Queue(connection=conn)
    

# Initialize Bot
from ffinstabot.config import secrets
BOT_TOKEN = secrets.get_var('BOT_TOKEN')
URL = secrets.get_var('SERVER_APP_DOMAIN')
PORT = int(os.environ.get('PORT', 5000))
from ffinstabot.bot import telebot

# set connection pool size for bot 
request = Request(con_pool_size=8)
q = mq.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)
telegram_bot = MQBot(BOT_TOKEN, request=request, mqueue=q)
updater = Updater(bot=telegram_bot, use_context=True)

# SET UP BOT COMMAND HANDLERS
telebot.setup(updater)
        