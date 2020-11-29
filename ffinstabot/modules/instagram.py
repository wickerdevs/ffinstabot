from datetime import datetime
from random import randrange

from instaclient.classes.instaobject import InstaBaseObject
from ffinstabot.classes.settings import Settings
from rq.job import Job
from rq.registry import DeferredJobRegistry, FailedJobRegistry, ScheduledJobRegistry, StartedJobRegistry, FinishedJobRegistry
from ffinstabot.modules import sheet
from ffinstabot import queue
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.follow_obj import Follow
from ffinstabot.texts import *

from telegram import ParseMode
from instaclient.errors.common import BlockedAccountError, InvaildPasswordError, InvalidUserError, PrivateAccountError, RestrictedAccountError, SuspisciousLoginAttemptError
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


def insta_update_calback(obj: Follow, message:str, message_id:int=None, timer:bool=False):
    """
    process_update_callback sends an update message to the user, to inform of the status of the current process. This method can be used as a callback in another method.

    Args:
        obj (ScraperorForwarder): Object to get the `chat_id` and `message_id` from.
        message (str): The text to send via message
        message_id (int, optional): If this argument is defined, then the method will try to edit the message matching the `message_id` of the `obj`. Defaults to None.
    """
    from ffinstabot import telegram_bot as bot
    if timer:
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
    insta_update_calback(follow, logging_in_text, follow.get_message_id())
    # Define client
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    # Scrape followers
    try:
        # LOGIN
        client.login(instasession.username, instasession.password)
        # SCRAPE
        follow.start_timer()
        followers = client.scrape_followers(follow.account, max_wait_time=350, callback=insta_update_calback, obj=follow, message=waiting_scrape_text, message_id=follow.get_message_id(), timer=True)
        # Initiating Follow
        insta_update_calback(follow, starting_follows_text.format(follow.account, follow.count), follow.get_message_id())
        # FOLLOW
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
    insta_update_calback(follow, logging_in_text, follow.get_message_id())
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    try:
        client.login(instasession.username, instasession.password)
    except (InvalidUserError, InvaildPasswordError):
        instasession.delete_creds()
        insta_update_calback(follow, invalid_credentials_text, follow.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(follow, verification_code_necessary, follow.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        bot.report_error(error)
        insta_update_calback(follow, operation_error_text, follow.get_message_id())
        return False

    insta_update_calback(follow, retriving_follows_text, follow.get_message_id())
    # Get Followed from GSheet Database
    follow.set_scraped(sheet.get_scraped(follow.get_user_id(), follow.get_account()))
    follow.set_followed(sheet.get_followed(follow.get_user_id(), follow.get_account()))
    
    
    # Unfollow Loop
    insta_update_calback(follow, initiating_unfollow_text, follow.get_message_id())
    follow.set_failed(list())
    for follower, index in enumerate(follow.get_followed()):
        try:
            client.unfollow_user(follower)
            follow.add_unfollowed(follower)
            logging.info(f'Unfollowed user <{follower}>')
            insta_update_calback(follow, unfollowed_user_text.format(len(follow.get_unfollowed()), len(follow.get_followed())), follow.get_message_id())
        except (RestrictedAccountError, BlockedAccountError):
            follow.add_failed(follow.get_followed()[index:])
            logging.warning(f'ACCOUNT HAS BEEN RESTRICTED')
        except:
            follow.add_failed(follower)
            logging.warning(f'Failed unfollowing user <{follower}>')

    # Discard driver
    client.__discard_driver()

    # Delete record from Database
    sheet.delete_follow(follow.get_user_id(), follow.get_account())

    text = unfollow_successful_text.format(len(follow.get_unfollowed()), len(follow.get_followed()))
    if len(follow.get_failed()) > 0:
        text += '\n<b>Failed:</b>'
        for user in follow.get_failed():
            text += f'\n- <a href="https://www.instagram.com/{user}">{user}</a>'

    insta_update_calback(follow, text, follow.get_message_id())
    return True


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
    # Get Notifs from Database
    last_notification = sheet.get_notification(settings.get_user_id())
    # Init & Login 
    insta_update_calback(settings, logging_in_text, settings.get_message_id())
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debut=True, error_callback=insta_error_callback)

    from ffinstabot import telegram_bot as bot

    try:
        client.login(instasession.username, instasession.password)
    except (InvalidUserError, InvaildPasswordError):
        instasession.delete_creds()
        insta_update_calback(settings, invalid_credentials_text, settings.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        insta_update_calback(settings, verification_code_necessary, settings.get_message_id())
        return False
    except Exception as error:
        bot.report_error(error)
        insta_update_calback(settings, operation_error_text, settings.get_message_id())
        return False
    # Scrape New Notifications
    try:
        notifications = client.check_notifications([InstaBaseObject.GRAPH_FOLLOW], 50)
        if len(notifications) < 1:
            # No notifications found
            return False
    except Exception as error:
        bot.report_error(error)
        insta_update_calback(settings, operation_error_text, settings.get_message_id())
        return False

    # Confront notifications
    new_notifs = list()
    notifications = sorted(notifications)
    if last_notification is None:
        # No last notification found
        pass
    elif notifications == []:
        # No New notifications
        print()
        return
    else:
        for notification, index in enumerate(notifications):
            if notification == last_notification:
                new_notifs = notifications[index:]
                break

    # Follow new users & send message
    for notification, index in enumerate(new_notifs):
        try:
            client.send_dm(notification.from_user.username, settings.get_text())
            time.sleep(randrange(25-45))
        except PrivateAccountError:
            pass
        except (RestrictedAccountError, BlockedAccountError):
            pass
        except Exception as error:
            pass

    # Save Last Notification
    last_notification = notifications[len(notifications)-1]
    sheet.set_notification(settings.get_user_id(), last_notification)