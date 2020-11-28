from datetime import datetime
from ffinstabot.classes.settings import Settings
from rq.job import Job
from rq.registry import DeferredJobRegistry, FailedJobRegistry, ScheduledJobRegistry, StartedJobRegistry, FinishedJobRegistry
from ffinstabot.modules import sheet
from ffinstabot import queue
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.follow_obj import Follow
from ffinstabot.texts import *

from telegram import ParseMode
from instaclient.errors.common import BlockedAccountError, InvaildPasswordError, InvalidUserError, PrivateAccountError, RestrictedAccountError
from instaclient import InstaClient
from instaclient import errors
import os, time, logging, random, string


FOLLOW = 'follow'
UNFOLLOW = 'unfollow'
CHECKNOTIFS = 'checknotifs'


def random_string():
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(6)))
    return result_str


def check_job_queue():
    """
    Checks if any jobs are running in the RQ Queue. If that's the case, returns True
    """
    # Check if no other job is in queue
    registry = StartedJobRegistry(queue=queue)
    if len(registry.get_job_ids()) > 0:
        return True
    else:
        return False


def insta_error_callback(driver):
    pass


def insta_update_calback(obj: Follow, message:str, message_id:int=None):
    """
    process_update_callback sends an update message to the user, to inform of the status of the current process. This method can be used as a callback in another method.

    Args:
        obj (ScraperorForwarder): Object to get the `chat_id` and `message_id` from.
        message (str): The text to send via message
        message_id (int, optional): If this argument is defined, then the method will try to edit the message matching the `message_id` of the `obj`. Defaults to None.
    """
    from ffinstabot import telegram_bot as bot
    message = message.format(obj.loop_timer())
    if message_id:
        try:
            bot.edit_message_text(text=message, chat_id=obj.user_id, message_id=message_id, parse_mode=ParseMode.HTML)
            return
        except: pass
    bot.send_message(obj.user_id, text=message, parse_mode=ParseMode.HTML)
    return


############################ FOLLOW JOBS ##############################
def enqueue_follow(follow:Follow, instasession:InstaSession):
    if os.environ.get('PORT') not in (None, ""):
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(FOLLOW, follow.account, identifier)
        job = Job.create(follow_job, kwargs={'follow': follow, 'instasession': instasession}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
    else:
        result = follow_job(follow, instasession)
        return result


def follow_job(follow:Follow, instasession:InstaSession) -> bool:
    # Define client
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    # Scrape followers
    try:
        client.login(instasession.username, instasession.password)
        follow.start_timer()
        followers = client.scrape_followers(follow.account, max_wait_time=350, callback=insta_update_calback, obj=follow, message=waiting_scrape_text, message_id=follow.get_message_id())
        insta_update_calback(follow, starting_follows_text.format(follow.account, follow.count), follow.get_message_id())
        for follower, index in enumerate(followers):
            try:
                logging.info(f'Following user <{follower}>')
                client.follow_user(follower)
                logging.debug('Followed a user.')
                insta_update_calback(follow, followed_user_text.format(index+1, follow.count), follow.get_message_id())
                follow.add_followed(follower)
            except PrivateAccountError:
                logging.debug('Followed a user.')
                insta_update_calback(follow, followed_user_text.format(index+1, follow.count), follow.get_message_id())
                follow.add_followed(follower)
            except (RestrictedAccountError, BlockedAccountError) as error:
                logging.warning('ACCOUNT HAS BEEN RESTRICTED')   
                follow.add_failed(followers[index:])
                insta_update_calback(follow, restricted_account_text, follow.get_message_id())
                break
            except Exception as error:
                logging.warning(f'An error occured when following a user <{follower}>: ', error)
                follow.add_failed(follower)
            time.sleep(30)
        client.__discard_driver()
        # Save followed list onto GSheet Database
        sheet.save_follows(follow.user_id, follow.account, follow.get_scraped(), follow.get_followed())
        insta_update_calback(follow, follow_successful_text.format(len(follow.get_followed()), follow.account), follow.get_message_id())
        return True

    except (InvalidUserError, InvaildPasswordError):
        instasession.delete_creds()
        insta_update_calback(follow, invalid_credentials_text, follow.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(follow, verification_code_necessary, follow.get_message_id())
        return False
    except errors.PrivateAccountError as error:
        insta_update_calback(follow, private_account_error_text, follow.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        bot.report_error(error)
        insta_update_calback(follow, operation_error_text, follow.get_message_id())
        return False


############################ UNFOLLOW JOBS ##############################
def enqueue_unfollow(follow:Follow, instasession:InstaSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        logging.info('Enqueueing Unfollow Job')
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(UNFOLLOW, follow.account, identifier)
        job = Job.create(follow_job, kwargs={'follow': follow, 'instasession': instasession}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
        return True
    else:
        logging.info('Running Enqueueing Job Locally')
        result = unfollow_job(follow, instasession)
        return result


def unfollow_job(follow:Follow, instasession:InstaSession) -> bool:
    # Define Client & Log In
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)
    # Get Followed from GSheet Database
    follow.set_scraped(sheet.get_scraped(follow.get_user_id(), follow.get_account()))
    follow.set_followed(sheet.get_followed(follow.get_user_id(), follow.get_account()))
    
    # Unfollow Loop
    for follower, index in enumerate(follow.get_followed()):
        pass
    # Discard driver
    # Delete record from Database


############################ NOTIFICATIONS JOBS ##############################
def enqueue_checknotifs(settings:Settings, instasession:InstaSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        logging.info('Enqueueing CheckNotifs Job')
        identifier = random_string()
        scrape_id = '{}:{}:{}'.format(CHECKNOTIFS, settings.account, identifier)
        job = Job.create(follow_job, kwargs={'settings': settings, 'instasession': instasession}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job)
        return True
    else:
        logging.info('Running CheckNotifs Job Locally')
        result = checknotifs_job(settings, instasession)
        return result


def schedule_checknotifs(settings:Settings, instasession:InstaSession) -> bool:
    pass


def checknotifs_job(settings:Settings, instasession:InstaSession) -> bool:
    pass