from datetime import datetime
from random import randrange
from instaclient.instagram.notification import Notification

from rq.job import Job
from rq.registry import DeferredJobRegistry, FailedJobRegistry, ScheduledJobRegistry, StartedJobRegistry, FinishedJobRegistry
from ffinstabot.modules import sheet
from ffinstabot import queue, applogger, instalogger
from ffinstabot.classes.instasession import InstaSession
from ffinstabot.classes.followsession import FollowSession
from ffinstabot.texts import *
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ffinstabot.classes.settings import Settings

from telegram import ParseMode
from telegram.error import BadRequest

from instaclient.errors.common import BlockedAccountError, FollowRequestSentError, InvaildPasswordError, InvalidUserError, PrivateAccountError, RestrictedAccountError, SuspisciousLoginAttemptError
from instaclient.client.instaclient import InstaClient
from instaclient.instagram.instaobject import InstaBaseObject
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
    driver.save_screenshot('error.png')
    from ffinstabot import telegram_bot as bot, secrets
    users_str = secrets.get_var('DEVS')
    if isinstance(users_str, str):
        users_str = users_str.replace('[', '')
        users_str = users_str.replace(']', '')
        users_str = users_str.replace(' ', '')
        users = users_str.split(',')
        for index, user in enumerate(users):
            users[index] = int(user)
    else:
        users = users_str

    for dev in users:
        bot.send_photo(chat_id=dev, photo=open('{}.png'.format('error'), 'rb'), caption='There was an error with the bot. Check logs')


def init_client():
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path='ffinstabot/config/driver/chromedriver.exe', debug=True, error_callback=insta_error_callback, logger=instalogger, localhost_headless=True)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debug=True, error_callback=insta_error_callback, logger=instalogger)
    return client


def insta_update_calback(obj: FollowSession, message:str, message_id:int=None, timer:bool=False, intentional:bool=True, scraped=None):
    """
    process_update_callback sends an update message to the user, to inform of the status of the current process. This method can be used as a callback in another method.

    Args:
        obj (ScraperorForwarder): Object to get the `chat_id` and `message_id` from.
        message (str): The text to send via message
        message_id (int, optional): If this argument is defined, then the method will try to edit the message matching the `message_id` of the `obj`. Defaults to None.
    """
    if intentional:
        from ffinstabot import telegram_bot as bot

        if scraped:
            message = message.format(len(scraped))
        
        if not message_id:
            message_id = sheet.get_message(obj.get_user_id())
        try:
            bot.delete_message(chat_id=obj.user_id, message_id=message_id)
        except Exception as error:
            applogger.error(f'Unable to delete message of id {message_id}', exc_info=error)
            pass         
    
        message_obj = bot.send_message(chat_id=obj.user_id, text=message, parse_mode=ParseMode.HTML)
        obj.set_message(message_obj.message_id)
        sheet.set_message(obj.user_id, message_obj.message_id)
        applogger.debug(f'Sent message of id {message_obj.message_id}')
        return    


############################ FOLLOW JOBS ##############################
def enqueue_follow(session:FollowSession):
    if os.environ.get('PORT') not in (None, ""):
        """ identifier = random_string()
        scrape_id = '{}:{}:{}'.format(FOLLOW, session.target, identifier)
        job = Job.create(follow_job, kwargs={'session': session}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job) """
        result = follow_job(session)
        return result
    else:
        result = follow_job(session)
        return result


def follow_job(session:FollowSession) -> bool:
    insta_update_calback(session, logging_in_text, session.get_message_id())
    # Define client
    client = init_client()

    # Scrape followers
    try:
        # LOGIN
        session.get_creds()
        client.login(session.username, session.password)

        # SCRAPE
        followers = client.get_followers(session.target, session.count, use_api=True, callback_frequency=25, callback=insta_update_calback, obj=session, message=waiting_scrape_text, message_id=session.get_message_id(), timer=True)
        session.set_scraped(followers)

        
        # Initiating Follow
        insta_update_calback(session, starting_follows_text.format(session.target, session.count), session.get_message_id())
        # FOLLOW
        for index, follower in enumerate(followers):
            if index > session.count-1:
                break
            try:
                applogger.info(f'Following user <{follower}>')
                client.follow(follower)
                applogger.debug('Followed a user.')
                insta_update_calback(session, followed_user_text.format(index+1, session.count), session.get_message_id())
                session.add_followed(follower)
            except (PrivateAccountError, FollowRequestSentError):
                applogger.debug('Followed a user.')
                insta_update_calback(session, followed_user_text.format(index+1, session.count), session.get_message_id())
                session.add_followed(follower)
            except (RestrictedAccountError, BlockedAccountError) as error:
                applogger.warning('ACCOUNT HAS BEEN RESTRICTED')   
                session.add_failed(followers[index:])
                insta_update_calback(session, restricted_account_text, session.get_message_id())
                break
            except Exception as error:
                applogger.warning(f'An error occured when following a user <{follower}>: ', error)
                session.add_failed(follower)
            if index < len(followers)-1:
                applogger.info('Followed user <{}>... Waiting...'.format(follower))
                time.sleep(randrange(10, 30))
        client.disconnect()
        # Save followed list onto GSheet Database
        sheet.save_follows(session)
        insta_update_calback(session, follow_successful_text.format(len(session.get_followed()), session.target), session.get_message_id())
        applogger.info('Done following {} users.'.format(len(session.get_followed())))
        return True

    except (InvalidUserError, InvaildPasswordError):
        client.disconnect()
        session.delete_creds()
        insta_update_calback(session, invalid_credentials_text, session.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        client.disconnect()
        insta_update_calback(session, verification_code_necessary, session.get_message_id())
        return False
    except errors.PrivateAccountError as error:
        client.disconnect()
        insta_update_calback(session, private_account_error_text, session.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        client.disconnect()
        applogger.error('An error occured: {}'.format(error), exc_info=error)
        bot.report_error(error)
        insta_update_calback(session, operation_error_text, session.get_message_id())
        return False


############################ UNFOLLOW JOBS ##############################
def enqueue_unfollow(session:FollowSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        applogger.info('Enqueueing Unfollow Job')
        """ identifier = random_string()
        scrape_id = '{}:{}:{}'.format(UNFOLLOW, session.target, identifier)
        job = Job.create(follow_job, kwargs={'session': session}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job) """
        result = unfollow_job(session)
        return result
    else:
        applogger.info('Running Enqueueing Job Locally')
        result = unfollow_job(session)
        return result


def unfollow_job(session:FollowSession) -> bool:
    # Define Client & Log In
    insta_update_calback(session, logging_in_text, session.get_message_id())
    client = init_client()

    try:
        session.get_creds()
        client.login(session.username, session.password)
    except (InvalidUserError, InvaildPasswordError):
        client.disconnect()
        session.delete_creds()
        insta_update_calback(session, invalid_credentials_text, session.get_message_id())
        return False
    except errors.VerificationCodeNecessary as error:
        client.disconnect()
        insta_update_calback(session, verification_code_necessary, session.get_message_id())
        return False
    except Exception as error:
        from ffinstabot import telegram_bot as bot
        client.disconnect()
        applogger.error(error)
        bot.report_error(error)
        insta_update_calback(session, operation_error_text, session.get_message_id())
        return False

    insta_update_calback(session, retriving_follows_text, session.get_message_id())
    # Get Followed from GSheet Database

    # Unfollow Loop
    insta_update_calback(session, initiating_unfollow_text, session.get_message_id())
    session.set_failed(list())
    for index, follower in enumerate(session.get_followed()):
        try:
            client.unfollow(follower)
            session.add_unfollowed(follower)
            applogger.info(f'Unfollowed user <{follower}>')
            insta_update_calback(session, unfollowed_user_text.format(len(session.get_unfollowed()), len(session.get_followed())), session.get_message_id())
            time.sleep(randrange(10,20))
        except (RestrictedAccountError, BlockedAccountError):
            session.add_failed(session.get_followed()[index:])
            applogger.warning(f'ACCOUNT HAS BEEN RESTRICTED')
            break
        except Exception as error:
            session.add_failed(follower)
            applogger.warning(f'Failed unfollowing user <{follower}>: {error}')

    # Discard driver
    client.disconnect()

    # Delete record from Database
    sheet.delete_follow(session.get_user_id(), session.username, session.get_target())

    text = unfollow_successful_text.format(len(session.get_unfollowed()), len(session.get_followed()))
    if len(session.get_failed()) > 0:
        text += '\n<b>Failed:</b>'
        for user in session.get_failed():
            text += f'\n- <a href="https://www.instagram.com/{user}">{user}</a>'

    insta_update_calback(session, text, session.get_message_id())
    return True


############################ NOTIFICATIONS JOBS ##############################
def enqueue_checknotifs(settings:'Settings', instasession:InstaSession) -> bool:
    if os.environ.get('PORT') not in (None, ""):
        applogger.info('Enqueueing CheckNotifs Job')
        """ identifier = random_string()
        scrape_id = '{}:{}:{}'.format(CHECKNOTIFS, instasession.user_id, identifier)
        job = Job.create(checknotifs_job, kwargs={'settings': settings, 'instasession': instasession, 'intentional': True}, id=scrape_id, timeout=3600, ttl=None, connection=queue.connection)
        queue.enqueue_job(job) """
        result = checknotifs_job(settings, instasession, intentional=True)
        return result
    else:
        applogger.info('Running CheckNotifs Job Locally')
        result = checknotifs_job(settings, instasession, intentional=True)
        return result


def schedule_checknotifs(settings:'Settings', instasession:InstaSession) -> bool:
    pass


def checknotifs_job(settings:'Settings', instasession:InstaSession, intentional:bool) -> bool:
    applogger.info('Starting CheckNotifs Job')
    from ffinstabot import telegram_bot as bot
    # Get Notifs from Database
    last_notification = sheet.get_notification(settings.get_user_id())

    # Init & Login 
    insta_update_calback(settings, logging_in_text, settings.get_message_id(), intentional=intentional)
    client = init_client()
    applogger.info('Created Client')
    try:
        client.login(instasession.username, instasession.password)
        applogger.debug('Logged in')
    except (InvalidUserError, InvaildPasswordError):
        client.disconnect()
        instasession.delete_creds()
        insta_update_calback(settings, invalid_credentials_text, settings.get_message_id(), intentional=True)
        return False
    except errors.VerificationCodeNecessary as error:
        client.disconnect()
        insta_update_calback(settings, verification_code_necessary, settings.get_message_id(), intentional=True)
        return False
    except Exception as error:
        client.disconnect()
        applogger.error('Error when checking notifications: ', exc_info=error)
        bot.report_error(error)
        insta_update_calback(settings, operation_error_text, settings.get_message_id(), intentional=True)
        return False
    
    
    # Scrape New Notifications
    try:
        notifications = client.get_notifications([InstaBaseObject.GRAPH_FOLLOW], 50)
        if len(notifications) < 1:
            # No notifications found
            return False
        applogger.debug('Got Notifications')
    except Exception as error:
        client.disconnect()
        insta_update_calback(settings, operation_error_text, settings.get_message_id(), intentional=True)
        applogger.error('Error when checking notifications: ', exc_info=error)
        bot.report_error(error)
        return False


    # Confront notifications
    new_notifs:List[Notification] = list()
    notifications = sorted(notifications)

    if last_notification is None:
        # No last notification found
        applogger.debug('Set last notification in GSheet for first time.')
        last_notification = notifications[len(notifications)-1]
        sheet.set_notification(settings.get_user_id(), last_notification)
        client.disconnect()
        insta_update_calback(settings, no_new_notifications_found_text, settings.message_id, intentional=intentional)
        return True
    elif notifications == []:
        # No New notifications
        client.disconnect()
        insta_update_calback(settings, no_new_notifications_found_text, settings.get_message_id(), intentional=intentional)
        return True
    else:
        for index, notification in enumerate(notifications):
            if notification == last_notification:
                for noti in notifications[index+1:]:
                    new_notifs.append(noti)
                break
    applogger.debug('LAST NOTIF: {}'.format(last_notification))
    applogger.debug('NEW NOTIFICATIONS: {}'.format(new_notifs))
    if len(new_notifs) > 0:
        insta_update_calback(settings, found_notifications_text.format(len(new_notifs)), settings.get_message_id(), intentional=intentional)
        

    # Follow new users & send message
    failed = list()
    success = list()
    for index, notification in enumerate(new_notifs):
        try:
            client.send_dm(notification.from_user.username, settings.get_setting(instasession.username).get_text())
            success.append(notification.from_user.username)
            applogger.info(f'Sent greetings message to <{notification.from_user.username}>')
            time.sleep(randrange(25,45))
        except PrivateAccountError:
            failed.append(notification.from_user.username)
            applogger.info(f'Did not send message to <{notification.from_user.username}> as account is Private.')
            continue
        except (RestrictedAccountError, BlockedAccountError) as error:
            applogger.warn('RESTRICTED OR BLOCKED ACCOUNT: \n{}'.format(error), exc_info=error)
            # Cancel Schedules for 24 hours
            """ registry = ScheduledJobRegistry(queue=queue)
            now = datetime.utcnow()
            ids = registry.get_job_ids()
            for id in ids:
                job = queue.fetch_job(id)
                enqueue_time = job.enqueued_at
                
                # Check if job is within 24 hour range to cancel
                job.cancel() """
            # Add failed
            failed.append(new_notifs[index:])
            client.disconnect()
            # Set last notification to last successful processed notification
            if index != 0:
                last = new_notifs[index-1]
                sheet.set_notification(settings.get_user_id(), last)
            return False
        except Exception as error:
            # Add failed
            applogger.debug('Error when following users', exc_info=error)
            failed.append(notification.from_user.username)
            applogger.error('Error when sending message to user (continued): ', exc_info=error)
            bot.report_error(error)
            continue
    client.disconnect()
    
    # Save Last Notification
    applogger.debug('Set last notification in GSheet')
    last_notification = notifications[len(notifications)-1]
    sheet.set_notification(settings.get_user_id(), last_notification)

    # Notify User of Operation Result
    if len(new_notifs) < 1:
        insta_update_calback(settings, checked_notis_no_followers, settings.get_message_id(), intentional=True)
    else:
        text = finished_notifications_text.format(len(success))
        if len(failed) > 0:
            text += inform_of_failed_text
            for user in failed:
                text += f'\n<a href="https://www.instagram.com/{user}/">{user}</a>'
        insta_update_calback(settings, text, settings.get_message_id(), intentional=True)
